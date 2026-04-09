import base64
import json
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

import requests
from django.core.cache import cache
from django.utils import timezone

from apps.commands.gpt.models import ProfileGPTSettings
from apps.shared.exceptions import PWarning
from petrovich.settings import env

logger = logging.getLogger("api")

OPENAI_OAUTH_CLIENT_ID = env.str("OPENAI_OAUTH_CLIENT_ID", default="app_EMoamEEZ73f0CkXaXp7hrann")
OPENAI_AUTH_BASE_URL = env.str("OPENAI_AUTH_BASE_URL", default="https://auth.openai.com").rstrip("/")
OPENAI_DEVICE_PAGE_URL = f"{OPENAI_AUTH_BASE_URL}/codex/device"
OPENAI_DEVICE_USER_CODE_URL = f"{OPENAI_AUTH_BASE_URL}/api/accounts/deviceauth/usercode"
OPENAI_DEVICE_TOKEN_URL = f"{OPENAI_AUTH_BASE_URL}/api/accounts/deviceauth/token"
OPENAI_OAUTH_TOKEN_URL = f"{OPENAI_AUTH_BASE_URL}/oauth/token"
OPENAI_DEVICE_CALLBACK_URL = f"{OPENAI_AUTH_BASE_URL}/deviceauth/callback"

OPENAI_OAUTH_SCOPE = "openid profile email offline_access"
OAUTH_REFRESH_MARGIN_SECONDS = 5 * 60
OAUTH_DEVICE_FLOW_TIMEOUT_SECONDS = 15 * 60
OAUTH_STATE_CACHE_TIMEOUT_SECONDS = 24 * 60 * 60


@dataclass(slots=True)
class ResolvedGPTAuth:
    auth_type: str
    access_token: str
    account_id: str | None = None


class OpenAIDeviceAuthCache:
    PRE_KEY = "gpt_openai_device_auth"

    def __init__(self, profile_gpt_settings_id: int):
        self.profile_gpt_settings_id = profile_gpt_settings_id

    def _get_key(self) -> str:
        return f"{self.PRE_KEY}_{self.profile_gpt_settings_id}"

    def get(self) -> dict:
        return cache.get(self._get_key(), {})

    def set(self, data: dict, timeout: int = OAUTH_STATE_CACHE_TIMEOUT_SECONDS) -> None:
        cache.set(self._get_key(), data, timeout=timeout)

    def clear(self) -> None:
        cache.delete(self._get_key())


def user_has_gpt_auth(profile, provider) -> bool:
    from apps.commands.gpt.utils import get_gpt_provider

    provider_model = get_gpt_provider(provider)
    try:
        profile_gpt_settings = profile.gpt_settings.get(provider=provider_model)
    except ProfileGPTSettings.DoesNotExist:
        return False
    return profile_gpt_settings.has_any_auth()


def extract_openai_account_id(id_token: str | None = None, access_token: str | None = None) -> str | None:
    for token in [id_token, access_token]:
        if not token or "." not in token:
            continue
        try:
            payload_b64 = token.split(".")[1]
            payload_b64 += "=" * (-len(payload_b64) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        except Exception:
            continue

        if account_id := payload.get("chatgpt_account_id"):
            return account_id

        if account_id := payload.get("https://api.openai.com/auth", {}).get("chatgpt_account_id"):
            return account_id

        organizations = payload.get("organizations", [])
        if organizations and (account_id := organizations[0].get("id")):
            return account_id
    return None


def _get_request_headers(user_agent: str = "petrovich-openai-oauth/1.0.0") -> dict[str, str]:
    return {
        "User-Agent": user_agent,
        "Accept": "application/json",
    }


def _log_non_ok_response(response, log_filter=None):
    try:
        payload = response.json()
    except Exception:
        payload = response.text
    logger.error(
        {
            "response": payload,
            "status_code": response.status_code,
            "url": str(response.url),
            "log_filter": log_filter,
        }
    )


def request_openai_device_user_code(log_filter=None) -> dict:
    response = requests.post(
        OPENAI_DEVICE_USER_CODE_URL,
        headers={
            **_get_request_headers(),
            "Content-Type": "application/json",
        },
        json={"client_id": OPENAI_OAUTH_CLIENT_ID},
        timeout=30,
    )

    if response.status_code == 404:
        raise PWarning(
            "В вашем аккаунте/воркспейсе OpenAI выключена авторизация через device code. "
            "Включите её в настройках безопасности Codex и попробуйте снова"
        )
    if not response.ok:
        _log_non_ok_response(response, log_filter=log_filter)
        raise PWarning("Не получилось начать OpenAI OAuth авторизацию")

    data = response.json()
    user_code = data.get("user_code") or data.get("usercode")
    if not user_code or not data.get("device_auth_id"):
        logger.error({"response": data, "log_filter": log_filter})
        raise PWarning("OpenAI вернул неполный ответ для device code авторизации")
    return data


def exchange_openai_authorization_code(
    authorization_code: str,
    code_verifier: str,
    log_filter=None,
) -> dict:
    response = requests.post(
        OPENAI_OAUTH_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "client_id": OPENAI_OAUTH_CLIENT_ID,
            "code": authorization_code,
            "code_verifier": code_verifier,
            "redirect_uri": OPENAI_DEVICE_CALLBACK_URL,
        },
        timeout=30,
    )
    if not response.ok:
        _log_non_ok_response(response, log_filter=log_filter)
        raise PWarning("Не получилось обменять authorization code на токены OpenAI")
    return response.json()


def refresh_openai_oauth_tokens(refresh_token: str, log_filter=None) -> dict:
    response = requests.post(
        OPENAI_OAUTH_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "refresh_token",
            "client_id": OPENAI_OAUTH_CLIENT_ID,
            "refresh_token": refresh_token,
            "scope": OPENAI_OAUTH_SCOPE,
        },
        timeout=30,
    )
    if not response.ok:
        _log_non_ok_response(response, log_filter=log_filter)
        raise PWarning("Не получилось обновить OpenAI OAuth токены")
    return response.json()


def resolve_profile_gpt_auth(profile_gpt_settings: ProfileGPTSettings, log_filter=None) -> ResolvedGPTAuth | None:
    active_auth_type = profile_gpt_settings.get_active_auth_type()
    if active_auth_type == ProfileGPTSettings.AuthType.API_KEY:
        api_key = profile_gpt_settings.get_key()
        return ResolvedGPTAuth(auth_type=active_auth_type, access_token=api_key)

    if active_auth_type == ProfileGPTSettings.AuthType.OAUTH_DEVICE:
        if profile_gpt_settings.oauth_needs_refresh(OAUTH_REFRESH_MARGIN_SECONDS):
            refresh_token = profile_gpt_settings.get_oauth_refresh_token()
            if not refresh_token:
                raise PWarning("OpenAI OAuth нужно переподключить: отсутствует refresh token")

            try:
                tokens = refresh_openai_oauth_tokens(refresh_token, log_filter=log_filter)
            except PWarning as exc:
                profile_gpt_settings.oauth_last_error = exc.msg
                profile_gpt_settings.save(update_fields=["oauth_last_error"])
                raise
            access_token = tokens.get("access_token")
            next_refresh_token = tokens.get("refresh_token") or refresh_token
            id_token = tokens.get("id_token") or profile_gpt_settings.get_oauth_id_token()
            account_id = extract_openai_account_id(id_token=id_token, access_token=access_token)
            if not access_token:
                raise PWarning("OpenAI OAuth не вернул access token")

            profile_gpt_settings.set_oauth_tokens(
                access_token=access_token,
                refresh_token=next_refresh_token,
                id_token=id_token or "",
                account_id=account_id or profile_gpt_settings.oauth_account_id,
                expires_at=timezone.now() + timedelta(seconds=tokens.get("expires_in", 3600)),
                last_refresh_at=timezone.now(),
            )
            profile_gpt_settings.save()

        access_token = profile_gpt_settings.get_oauth_access_token()
        if not access_token:
            raise PWarning("OpenAI OAuth нужно переподключить: отсутствует access token")

        account_id = profile_gpt_settings.oauth_account_id or extract_openai_account_id(
            id_token=profile_gpt_settings.get_oauth_id_token(),
            access_token=access_token,
        )
        if account_id and profile_gpt_settings.oauth_account_id != account_id:
            profile_gpt_settings.oauth_account_id = account_id
            profile_gpt_settings.save(update_fields=["oauth_account_id"])
        return ResolvedGPTAuth(
            auth_type=active_auth_type,
            access_token=access_token,
            account_id=account_id,
        )

    return None


def get_openai_oauth_status(profile_gpt_settings: ProfileGPTSettings) -> dict:
    status = {
        "connected": profile_gpt_settings.get_active_auth_type() == ProfileGPTSettings.AuthType.OAUTH_DEVICE,
        "auth_type": profile_gpt_settings.get_active_auth_type(),
        "account_id": profile_gpt_settings.oauth_account_id,
        "expires_at": profile_gpt_settings.oauth_expires_at,
        "last_refresh_at": profile_gpt_settings.oauth_last_refresh_at,
        "last_error": profile_gpt_settings.oauth_last_error,
    }
    status.update(OpenAIDeviceAuthCache(profile_gpt_settings.id).get())
    return status


def start_openai_device_auth(
    profile_gpt_settings: ProfileGPTSettings,
    peer_id: int,
    message_thread_id: int | None,
    log_filter=None,
) -> dict:
    cache_obj = OpenAIDeviceAuthCache(profile_gpt_settings.id)
    current_state = cache_obj.get()
    if current_state.get("status") == "pending":
        expires_at = current_state.get("expires_at")
        try:
            if expires_at and datetime.fromisoformat(expires_at) > timezone.now():
                return current_state
        except ValueError:
            pass

    data = request_openai_device_user_code(log_filter=log_filter)
    interval = int(data.get("interval") or 5)
    expires_at = timezone.now() + timedelta(seconds=OAUTH_DEVICE_FLOW_TIMEOUT_SECONDS)
    state = {
        "status": "pending",
        "device_auth_id": data["device_auth_id"],
        "user_code": data.get("user_code") or data.get("usercode"),
        "verification_url": OPENAI_DEVICE_PAGE_URL,
        "interval": interval,
        "peer_id": peer_id,
        "message_thread_id": message_thread_id,
        "created_at": timezone.now().isoformat(),
        "expires_at": expires_at.isoformat(),
        "error": "",
    }
    cache_obj.set(state, timeout=OAUTH_DEVICE_FLOW_TIMEOUT_SECONDS + 60)

    threading.Thread(
        target=_poll_openai_device_auth,
        args=(profile_gpt_settings.id, state["device_auth_id"], log_filter),
        daemon=True,
    ).start()
    return state


def _poll_openai_device_auth(profile_gpt_settings_id: int, device_auth_id: str, log_filter=None) -> None:
    cache_obj = OpenAIDeviceAuthCache(profile_gpt_settings_id)
    start_time = time.time()

    while time.time() - start_time < OAUTH_DEVICE_FLOW_TIMEOUT_SECONDS:
        state = cache_obj.get()
        if not state or state.get("status") != "pending" or state.get("device_auth_id") != device_auth_id:
            return

        time.sleep(int(state.get("interval") or 5))

        try:
            response = requests.post(
                OPENAI_DEVICE_TOKEN_URL,
                headers={
                    **_get_request_headers(),
                    "Content-Type": "application/json",
                },
                json={
                    "device_auth_id": state["device_auth_id"],
                    "user_code": state["user_code"],
                },
                timeout=30,
            )
        except Exception as exc:
            logger.warning({"message": str(exc), "log_filter": log_filter})
            continue

        if response.status_code in (403, 404):
            continue

        if not response.ok:
            _log_non_ok_response(response, log_filter=log_filter)
            _set_openai_device_auth_error(cache_obj, "OpenAI отклонил авторизацию по device code")
            _notify_openai_auth_result(state, "Не получилось подключить OpenAI аккаунт")
            return

        payload = response.json()
        try:
            tokens = exchange_openai_authorization_code(
                authorization_code=payload["authorization_code"],
                code_verifier=payload["code_verifier"],
                log_filter=log_filter,
            )
        except PWarning as exc:
            _set_openai_device_auth_error(cache_obj, exc.msg)
            _notify_openai_auth_result(state, exc.msg)
            return

        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        id_token = tokens.get("id_token", "")
        account_id = extract_openai_account_id(id_token=id_token, access_token=access_token)

        if not access_token or not refresh_token:
            _set_openai_device_auth_error(cache_obj, "OpenAI OAuth вернул неполные токены")
            _notify_openai_auth_result(state, "OpenAI OAuth вернул неполные токены")
            return

        try:
            profile_gpt_settings = ProfileGPTSettings.objects.get(id=profile_gpt_settings_id)
        except ProfileGPTSettings.DoesNotExist:
            cache_obj.clear()
            return

        profile_gpt_settings.set_oauth_tokens(
            access_token=access_token,
            refresh_token=refresh_token,
            id_token=id_token,
            account_id=account_id or "",
            expires_at=timezone.now() + timedelta(seconds=tokens.get("expires_in", 3600)),
            last_refresh_at=timezone.now(),
        )
        profile_gpt_settings.save()

        success_state = {
            **state,
            "status": "connected",
            "connected_at": timezone.now().isoformat(),
            "error": "",
        }
        cache_obj.set(success_state)
        _notify_openai_auth_result(
            state,
            "Аккаунт OpenAI подключён. Через OAuth сейчас доступен обычный чат /gpt без API key",
        )
        return

    state = cache_obj.get()
    if not state or state.get("device_auth_id") != device_auth_id:
        return
    _set_openai_device_auth_error(cache_obj, "Время подтверждения OpenAI OAuth истекло")
    _notify_openai_auth_result(state, "Время подтверждения OpenAI OAuth истекло. Запустите /gpt oauth заново")


def _set_openai_device_auth_error(cache_obj: OpenAIDeviceAuthCache, error_text: str) -> None:
    state = cache_obj.get()
    if not state:
        return
    try:
        ProfileGPTSettings.objects.filter(id=cache_obj.profile_gpt_settings_id).update(oauth_last_error=error_text)
    except Exception:
        logger.exception("Failed to persist OpenAI OAuth error")
    cache_obj.set({**state, "status": "error", "error": error_text})


def _notify_openai_auth_result(state: dict, text: str) -> None:
    try:
        from apps.bot.core.bot.telegram.tg_bot import TgBot
        from apps.bot.core.messages.response_message import ResponseMessageItem

        bot = TgBot()
        rmi = ResponseMessageItem(
            text=text,
            peer_id=state.get("peer_id"),
            message_thread_id=state.get("message_thread_id"),
        )
        bot.send_response_message_item(rmi)
    except Exception as exc:
        logger.error({"message": str(exc), "state": state})

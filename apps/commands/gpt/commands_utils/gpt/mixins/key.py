from apps.bot.core.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.commands.gpt.api.base import GPTAPI
from apps.commands.gpt.enums import GPTProviderEnum
from apps.commands.gpt.models import ProfileGPTSettings
from apps.commands.gpt.oauth import (
    OpenAIDeviceAuthCache,
    start_openai_device_auth,
    get_openai_oauth_status,
    user_has_gpt_auth,
)
from apps.commands.gpt.protocols import GPTCommandProtocol
from apps.commands.help_text import HelpTextArgument
from apps.shared.exceptions import PWarning


class GPTKeyMixin(GPTCommandProtocol):
    KEY_HELP_TEXT_ITEMS = [
        HelpTextArgument("ключ (ключ)", "добавляет персональный API ключ"),
        HelpTextArgument("ключ удалить", "удаляет персональный API ключ"),
        HelpTextArgument("oauth", "подключает аккаунт OpenAI по подписке через device code"),
        HelpTextArgument("oauth статус", "показывает статус OpenAI OAuth подключения"),
        HelpTextArgument("oauth удалить", "отвязывает OpenAI OAuth аккаунт"),
    ]

    KEEP_YOUR_SECRET_KEY_IN_SAFE = (
        "Держите свой ключ в секрете. Я удалил ваше сообщение с ключом (или удалите сами если у меня нет прав)"
    )
    PROVIDE_API_KEY_TEMPLATE = (
        "Для использования {provider_name} укажите свой ключ (API_KEY)\n{command_name} ключ (ключ)"
    )
    PROVIDE_AUTH_TEMPLATE = (
        "Для использования {provider_name} укажите свой ключ (API_KEY) или подключите OpenAI аккаунт:\n"
        "{command_name} ключ (ключ)\n"
        "{command_name} oauth"
    )
    OAUTH_IS_PM_ONLY = "OpenAI OAuth подключается только в личке, чтобы не светить одноразовый код в чате"
    OAUTH_ONLY_TEXT_CHAT = (
        "Через OpenAI OAuth сейчас доступен только обычный чат /gpt. Картинки и аудио требуют API key"
    )

    # MENU

    def menu_key(self) -> ResponseMessageItem:
        """
        Установка/удаление персонального ключа ChatGPT
        """

        self.check_args(2)
        arg = self.event.message.args_case[1]

        profile_gpt_settings = self.get_profile_gpt_settings()

        if arg.lower() in ["удалить", "сброс", "сбросить", "delete", "reset"]:
            profile_gpt_settings.set_key("")
            profile_gpt_settings.save()
            rmi = ResponseMessageItem(text="Удалил ваш ключ")
        else:
            if self.event.is_from_chat:
                self.bot.delete_messages(self.event.chat.chat_id, self.event.message.id)
                self._set_key(profile_gpt_settings, arg)
                raise PWarning(self.KEEP_YOUR_SECRET_KEY_IN_SAFE)
            self._set_key(profile_gpt_settings, arg)
            rmi = ResponseMessageItem(text="Добавил новый ключ")

        return rmi

    def menu_oauth(self) -> ResponseMessageItem:
        if not self.event.is_from_pm:
            raise PWarning(self.OAUTH_IS_PM_ONLY)
        profile_gpt_settings = self.get_profile_gpt_settings()
        current_status = get_openai_oauth_status(profile_gpt_settings)

        if len(self.event.message.args) > 1:
            arg = self.event.message.args[1]
            if arg in ["удалить", "сброс", "сбросить", "delete", "reset"]:
                OpenAIDeviceAuthCache(profile_gpt_settings.id).clear()
                profile_gpt_settings.clear_oauth_tokens()
                profile_gpt_settings.save()
                return ResponseMessageItem(text="Удалил OpenAI OAuth подключение")
            if arg in ["статус", "status", "info", "инфо"]:
                return ResponseMessageItem(text=self._get_oauth_status_text(profile_gpt_settings))

        if current_status.get("connected") and current_status.get("status") != "pending":
            return ResponseMessageItem(text=self._get_oauth_status_text(profile_gpt_settings))

        state = start_openai_device_auth(
            profile_gpt_settings,
            peer_id=self.event.peer_id,
            message_thread_id=self.event.message_thread_id,
            log_filter=self.event.log_filter,
        )
        text = (
            "OpenAI OAuth авторизация запущена\n\n"
            f"1. Откройте {self.bot.get_formatted_url('эту ссылку', state['verification_url'])}\n"
            f"2. Введите код: {self.bot.get_formatted_text_line(state['user_code'])}\n"
            "3. После подтверждения я напишу сюда сам\n\n"
            "Важно: device code — одноразовый чувствительный код. Не пересылайте его другим людям.\n\n"
            f"{self.OAUTH_ONLY_TEXT_CHAT}"
        )
        return ResponseMessageItem(text=text)

    # COMMON UTILS

    def check_key(self) -> ResponseMessage | None:
        if self.event.message.args and self.event.message.args[0] in ["ключ", "key"]:
            return ResponseMessage(self.menu_key())
        if self.event.message.args and self.event.message.args[0] == "oauth":
            return ResponseMessage(self.menu_oauth())

        has_access = user_has_gpt_auth(self.event.sender, self.provider)
        if not has_access:
            error_msg = self.PROVIDE_AUTH_TEMPLATE.format(
                provider_name=self.provider.type_enum,
                command_name=self.bot.get_formatted_text_line(f"/{self.name}"),
            )
            raise PWarning(error_msg)
        return None

    @staticmethod
    def raise_no_access_exception(gpt_type_enum: GPTProviderEnum, command_name: str) -> None:
        error_msg = GPTKeyMixin.PROVIDE_API_KEY_TEMPLATE.format(provider_name=gpt_type_enum, command_name=command_name)
        raise PWarning(error_msg)

    # UTILS

    def _set_key(self, profile_gpt_settings: ProfileGPTSettings, api_key: str):
        gpt_api: GPTAPI = self.provider.api_class(
            api_key=api_key,
            log_filter=self.event.log_filter,
        )
        if not gpt_api.check_key():
            raise PWarning("Невалидный ключ")
        profile_gpt_settings.set_key(api_key)
        profile_gpt_settings.save()

    def _get_oauth_status_text(self, profile_gpt_settings: ProfileGPTSettings) -> str:
        status = get_openai_oauth_status(profile_gpt_settings)
        state_status = status.get("status")
        if state_status == "pending":
            return (
                "OpenAI OAuth ещё ждёт подтверждения\n\n"
                f"Ссылка: {self.bot.get_formatted_url('открыть', status.get('verification_url'))}\n"
                f"Код: {self.bot.get_formatted_text_line(str(status.get('user_code')))}\n"
                f"Истекает: {status.get('expires_at')}"
            )
        if state_status == "error":
            return f"OpenAI OAuth завершился ошибкой\n\n{status.get('error')}"
        if status.get("connected"):
            expires_at = status.get("expires_at")
            account_id = status.get("account_id") or "{unknown}"
            return (
                "OpenAI OAuth подключён\n\n"
                f"Account ID: {self.bot.get_formatted_text_line(str(account_id))}\n"
                f"Токен действует до: {expires_at}\n\n"
                f"{self.OAUTH_ONLY_TEXT_CHAT}"
            )
        return "OpenAI OAuth ещё не подключён"

import base64
import json

from django.test import SimpleTestCase

from apps.bot.models import Profile
from apps.commands.gpt.models import ProfileGPTSettings, Provider
from apps.commands.gpt.oauth import extract_openai_account_id


def _build_jwt(payload: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{header}.{body}.signature"


class GPTAuthTestCase(SimpleTestCase):
    def _get_settings(self) -> ProfileGPTSettings:
        return ProfileGPTSettings(profile=Profile(), provider=Provider(name="chatgpt"))

    def test_legacy_key_fallback_marks_api_key_auth(self):
        settings = self._get_settings()
        settings.set_key("sk-test")
        settings.auth_type = ""

        self.assertEqual(settings.get_active_auth_type(), ProfileGPTSettings.AuthType.API_KEY)
        self.assertTrue(settings.has_any_auth())

    def test_clearing_key_falls_back_to_oauth(self):
        settings = self._get_settings()
        settings.set_key("sk-test")
        settings.set_oauth_tokens(
            access_token="access-token",
            refresh_token="refresh-token",
            account_id="acc_123",
        )

        settings.set_key("")

        self.assertEqual(settings.get_active_auth_type(), ProfileGPTSettings.AuthType.OAUTH_DEVICE)
        self.assertEqual(settings.get_oauth_access_token(), "access-token")

    def test_extract_openai_account_id_prefers_namespaced_claim(self):
        token = _build_jwt(
            {
                "https://api.openai.com/auth": {"chatgpt_account_id": "acc_456"},
                "organizations": [{"id": "org_1"}],
            }
        )

        self.assertEqual(extract_openai_account_id(id_token=token), "acc_456")

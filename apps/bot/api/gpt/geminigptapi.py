import requests
from requests import HTTPError

from apps.bot.api.gpt.gpt import GPTAPI
from apps.bot.api.gpt.message import GPTMessages
from apps.bot.api.gpt.response import GPTAPICompletionsResponse
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.proxy import get_proxies
from petrovich.settings import env


class GeminiGPTAPI(GPTAPI):
    API_KEY = env.str("GEMINI_API_KEY")

    DEFAULT_COMPLETIONS_MODEL: str = "gemini-1.5-pro"

    BASE_URL = "https://generativelanguage.googleapis.com/v1/models"
    URL = f"{BASE_URL}/{DEFAULT_COMPLETIONS_MODEL}:generateContent"

    def __init__(self, **kwargs):
        super(GeminiGPTAPI, self).__init__(**kwargs)

    def completions(self, messages: GPTMessages, use_image=False) -> GPTAPICompletionsResponse:
        data = {
            "contents": messages.get_messages(),
            "safetySettings": self._safety_settings
        }
        r = self._do_request(self.URL, json=data)
        answer = r.json()['candidates'][0]['content']['parts'][0]['text']
        r = GPTAPICompletionsResponse(
            text=answer
        )
        return r

    @property
    def _headers(self) -> dict:
        return {
            'Content-Type': 'application/json',
            'x-goog-api-key': self.API_KEY
        }

    def _do_request(self, url, **kwargs) -> requests.Response:
        r = self.requests.post(
            url,
            proxies=get_proxies(),
            headers=self._headers,
            **kwargs
        )
        try:
            r.raise_for_status()
        except HTTPError:
            raise PWarning("Какая-то ошибка API Gemini")
        return r

    @property
    def _safety_settings(self) -> list[dict]:
        return [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]

import base64

import requests
from requests import HTTPError

from apps.bot.api.gpt.gpt import GPTAPI
from apps.bot.api.gpt.message import GPTMessages, GeminiGPTMessage, GPTMessageRole
from apps.bot.api.gpt.models import GPTImageFormat
from apps.bot.api.gpt.response import GPTAPICompletionsResponse, GPTAPIImageDrawResponse
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.proxy import get_proxies
from petrovich.settings import env


class GeminiGPTAPI(GPTAPI):
    API_KEY = env.str("GEMINI_API_KEY")

    DEFAULT_MODEL: str = "gemini-2.0-flash"
    DEFAULT_DRAW_MODEL: str = 'gemini-2.0-flash-exp-image-generation'

    BASE_URL = "https://generativelanguage.googleapis.com/v1/models"
    BASE_BETA_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    URL = f"{BASE_URL}/{DEFAULT_MODEL}:generateContent"
    IMAGE_DRAW_URL = f"{BASE_BETA_URL}/{DEFAULT_DRAW_MODEL}:generateContent"

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

    def draw(self, prompt: str, gpt_image_format: GPTImageFormat, count: int = 1) -> GPTAPIImageDrawResponse:
        """
        Метод для рисования GPTAPI, переопределяется не у всех наследников
        """
        gpt_message = GeminiGPTMessage(role=GPTMessageRole.USER, text=prompt)

        data = {
            "contents": [gpt_message.get_message()],
            "safetySettings": self._safety_settings,
            "generationConfig": {"responseModalities": ["Text", "Image"]}
        }

        result = self._do_request(self.IMAGE_DRAW_URL, json=data).json()

        r = GPTAPIImageDrawResponse(
            images_bytes=[base64.b64decode(x['inlineData']['data']) for x in
                          result['candidates'][0]['content']['parts']],
            images_prompt=None
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

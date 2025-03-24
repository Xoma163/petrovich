import base64

import requests
from requests import HTTPError

from apps.bot.api.gpt.gpt import GPTAPI
from apps.bot.api.gpt.message import GPTMessages
from apps.bot.api.gpt.models import GPTImageFormat, GPTImageQuality
from apps.bot.api.gpt.response import GPTAPICompletionsResponse, GPTAPIImageDrawResponse
from apps.bot.classes.const.exceptions import PError
from apps.bot.utils.proxy import get_proxies
from petrovich.settings import env


class GeminiGPTAPI(GPTAPI):
    API_KEY = env.str("GEMINI_API_KEY")

    DEFAULT_MODEL: str = "gemini-2.0-flash"
    DEFAULT_DRAW_MODEL: str = 'imagen-3.0-generate-002'

    BASE_URL = "https://generativelanguage.googleapis.com/v1/models"
    BASE_BETA_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    URL = f"{BASE_URL}/{DEFAULT_MODEL}:generateContent"
    IMAGE_DRAW_URL = f"{BASE_BETA_URL}/{DEFAULT_DRAW_MODEL}:predict"

    ERRORS_MAP = {
        'Image generation failed with the following error: The prompt could not be submitted. Your current safety filter threshold prohibited one or more words in this prompt. If you think this was an error, send feedback.': "Gemini не может обработать запрос по политикам безопасности",
    }

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

    def draw(
            self,
            prompt: str,
            image_format: GPTImageFormat,
            quality: GPTImageQuality,  # not supported
            count: int = 1,
    ) -> GPTAPIImageDrawResponse:
        """
        Метод для рисования GPTAPI, переопределяется не у всех наследников
        """
        data = {
            "instances": {
                "prompt": prompt
            },
            "parameters": {
                "sampleCount": count,
                "person_generation": "ALLOW_ADULT"
            },
        }

        ratio_map = {
            GPTImageFormat.SQUARE: "1:1",
            GPTImageFormat.ALBUM: "16:9",
            GPTImageFormat.PORTAIR: "9:16",
        }
        if ratio_format := ratio_map.get(image_format):
            data['parameters']['aspect_ratio'] = ratio_format

        result = self._do_request(self.IMAGE_DRAW_URL, json=data).json()

        r = GPTAPIImageDrawResponse(
            images_bytes=[base64.b64decode(x['bytesBase64Encoded']) for x in result['predictions']],
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
            code = r.json().get('error', {}).get('message')
            error_str = self.ERRORS_MAP.get(code, "Какая-то ошибка API Gemini")
            raise PError(error_str)
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

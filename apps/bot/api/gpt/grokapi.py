import requests
from requests import HTTPError

from apps.bot.api.gpt.gpt import GPTAPI
from apps.bot.api.gpt.message import GrokGPTMessages
from apps.bot.api.gpt.models import GPTImageFormat
from apps.bot.api.gpt.response import GPTAPICompletionsResponse, GPTAPIImageDrawResponse
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.proxy import get_proxies
from petrovich.settings import env


class GrokGPTAPI(GPTAPI):
    API_KEY = env.str("GROK_API_KEY")

    DEFAULT_COMPLETIONS_MODEL: str = "grok-2-latest"
    DEFAULT_VISION_MODEL: str = "grok-2-vision-1212"
    DEFAULT_DRAW_MODEL: str = "grok-2-image-latest"

    BASE_URL = "https://api.x.ai/v1"
    COMPLETIONS_URL = f"{BASE_URL}/chat/completions"
    IMAGE_GEN_URL: str = f"{BASE_URL}/images/generations"

    def __init__(self, **kwargs):
        super(GrokGPTAPI, self).__init__(**kwargs)

    def completions(self, messages: GrokGPTMessages, use_image=False) -> GPTAPICompletionsResponse:
        data = {
            "messages": messages.get_messages(),
            "model": self._get_model(use_image),
        }
        r = self._do_request(self.COMPLETIONS_URL, json=data)
        answer = r.json()['choices'][0]['message']['content']
        r = GPTAPICompletionsResponse(
            text=answer
        )
        return r

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
            raise PWarning("Какая-то ошибка API Grok")
        return r

    def _get_model(self, use_image=False) -> str:
        if use_image:
            return self.DEFAULT_VISION_MODEL
        return self.DEFAULT_COMPLETIONS_MODEL

    @property
    def _headers(self) -> dict:
        return {
            'Authorization': f"Bearer {self.API_KEY}"
        }

    def draw(self, prompt: str, gpt_image_format: GPTImageFormat, count: int = 1) -> GPTAPIImageDrawResponse:
        """
        Метод для рисования GPTAPI, переопределяется не у всех наследников
        """
        data = {

            'prompt': prompt,
            'n': count,
            'response_format': 'url',
            'model': self.DEFAULT_DRAW_MODEL,
        }
        result = self._do_request(self.IMAGE_GEN_URL, json=data).json()

        image_prompt = result['data'][0]['revised_prompt']
        r = GPTAPIImageDrawResponse(
            images_url=[x['url'] for x in result['data']],
            images_prompt=image_prompt
        )
        return r

import os
import random
import re
import uuid

from apps.bot.api.gpt.gpt import GPT
from apps.bot.api.gpt.response import GPTAPICompletionsResponse, GPTAPIImageDrawResponse
from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PWarning
from petrovich.settings import env, BASE_DIR


class GigaChatGPTAPI(GPT, API):
    AUTH_DATA = env.str("GIGACHAT_AUTH_DATA")

    BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"
    COMPLETIONS_URL = f"{BASE_URL}/chat/completions"

    GOSUSLUGI_CERT_PATH = os.path.join(BASE_DIR, "secrets/certs/russian_trusted_root_ca_pem.crt")

    LATEST_MODEL = "GigaChat:latest"
    DEFAULT_MODEL = LATEST_MODEL

    def __init__(self, **kwargs):
        super(GigaChatGPTAPI, self).__init__(**kwargs)
        self.access_token = None

    def completions(self, messages) -> GPTAPICompletionsResponse:
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}"
        }

        data = {
            "model": self._get_model(),
            "max_tokens": 2048,
            "messages": messages,
            "function_call": "auto"
        }

        r = self.requests.post(
            f"{self.COMPLETIONS_URL}",
            json=data,
            headers=headers,
            verify=self.GOSUSLUGI_CERT_PATH
        )
        response = GPTAPICompletionsResponse(
            text=r.json()['choices'][0]['message']['content']
        )
        return response

    def draw(self, prompt) -> GPTAPIImageDrawResponse:
        messages = [{
            "role": "system",
            "content": "Если тебя просят создать изображение, ты должен сгенерировать специальный блок: "
                       "<fuse>text2image(query: str, style: str)</fuse>, где query — текстовое описание желаемого "
                       "изображения, style — необязательный параметр, задающий стиль изображения."
        },
            {'role': "user", 'content': prompt}
        ]
        res = self.completions(messages)

        src_regexp = r'src\s*=\s*"(.+?)"'
        r = re.compile(src_regexp)

        try:
            file_id = r.findall(res.text)[0]
        except Exception:
            raise PWarning(res.text)
        response = GPTAPIImageDrawResponse(
            images_bytes=self._get_file_by_id(file_id)
        )
        return response

    def _set_access_token(self):
        headers = {
            "Authorization": f"Bearer {self.AUTH_DATA}",
            "RqUID": str(uuid.uuid1(random.randint(0, 281474976710655)))  # 2^48-1
        }

        r = self.requests.post(
            "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
            data={'scope': "GIGACHAT_API_PERS"},
            headers=headers,
            verify=self.GOSUSLUGI_CERT_PATH,
            log=False
        )
        self.access_token = r.json()['access_token']

    def _get_access_token(self) -> str:
        if not self.access_token:
            self._set_access_token()
        return self.access_token

    def _get_model(self, use_image=False):
        return self.DEFAULT_MODEL

    def _get_file_by_id(self, file_id):
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}"
        }

        return self.requests.get(
            f"{self.BASE_URL}/files/{file_id}/content",
            headers=headers,
            verify=self.GOSUSLUGI_CERT_PATH,
            log=False
        ).content

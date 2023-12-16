import logging
import os
import random
import uuid

import requests

from petrovich.settings import env, BASE_DIR
from .gpt import GPT

logger = logging.getLogger('responses')


class GigaChat(GPT):
    AUTH_DATA = env.str("GIGACHAT_AUTH_DATA")

    BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"
    COMPLETIONS_URL = f"{BASE_URL}/chat/completions"

    GOSUSLUGI_CERT_PATH = os.path.join(BASE_DIR, "secrets/certs/russian_trusted_root_ca_pem.crt")

    LATEST_MODEL = "GigaChat:latest"
    PRO_MODEL = "GigaChat-Pro"

    def __init__(self, model):
        super().__init__(model)
        self.access_token = None

    def set_access_token(self):
        headers = {
            "Authorization": f"Bearer {self.AUTH_DATA}",
            "RqUID": str(uuid.uuid1(random.randint(0, 281474976710655)))  # 2^48-1
        }

        r = requests.post(
            "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
            data={'scope': "GIGACHAT_API_PERS"},
            headers=headers,
            verify=self.GOSUSLUGI_CERT_PATH
        )
        r_json = r.json()
        if r.status_code != 200:
            logger.error({"response": r_json})

        self.access_token = r_json['access_token']

    def get_access_token(self) -> str:
        if not self.access_token:
            self.set_access_token()
        return self.access_token

    def completions(self, messages) -> str:
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}"
        }

        data = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": messages
        }

        r = requests.post(
            f"{self.COMPLETIONS_URL}",
            json=data,
            headers=headers,
            verify=self.GOSUSLUGI_CERT_PATH
        )
        return r.json()['choices'][0]['message']['content']

import logging

import requests

from petrovich.settings import env
from .gpt import GPT

logger = logging.getLogger('responses')


class ChatGPTAPI(GPT):
    API_KEY = env.str("OPENAI_KEY")

    GPT_4 = 'gpt-4-1106-preview'
    GPT_4_VISION = 'gpt-4-vision-preview'
    GPT_3 = 'gpt-3.5-turbo-16k-0613'
    DALLE_3 = 'dall-e-3'
    DALLE_2 = 'dall-e-2'

    HEADERS = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    BASE_URL = "https://api.openai.com/v1"
    COMPLETIONS_URL = f"{BASE_URL}/chat/completions"
    IMAGE_GEN_URL = f"{BASE_URL}/images/generations"

    def completions(self, messages: list):
        payload = {
            "model": self.model,
            "messages": messages,
        }

        if self.model == self.GPT_4_VISION:
            payload['max_tokens'] = 1024

        r = requests.post(self.COMPLETIONS_URL, headers=self.HEADERS, json=payload)
        if r.status_code != 200:
            logger.debug({"response": r.text})
        r_json = r.json()

        answer = r_json['choices'][0]['message']['content']
        return answer

    def draw(self, promt: str, count=5):
        if self.model == self.DALLE_3:
            count = 1

        payload = {
            "model": self.model,
            "prompt": promt,
            "n": count,
            "size": "1792x1024",
            "quality": "hd"
        }

        r = requests.post(self.IMAGE_GEN_URL, headers=self.HEADERS, json=payload)
        if r.status_code != 200:
            logger.debug({"response": r.text})
        r_json = r.json()

        return [x['url'] for x in r_json['data']]

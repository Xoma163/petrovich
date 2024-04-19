from json import JSONDecodeError

from apps.bot.api.gpt.gpt import GPT
from apps.bot.api.gpt.response import GPTAPIResponse
from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PWarning, PError
from apps.bot.models import Profile
from petrovich.settings import env


class ChatGPTAPI(GPT, API):
    API_KEY = env.str("OPENAI_KEY")

    GPT_4 = 'gpt-4-0125-preview'
    GPT_4_VISION = 'gpt-4-vision-preview'
    GPT_3 = 'gpt-3.5-turbo-16k-0613'
    DALLE_3 = 'dall-e-3'
    DALLE_2 = 'dall-e-2'

    DALLE_3_IMAGE_COST = 0.120
    DALLE_2_IMAGE_COST = 0.020

    GPT_4_PROMPT_TOKEN_COST = 0.00001
    GPT_4_COMPLETION_TOKEN_COST = 0.00003

    GPT_3_PROMPT_TOKEN_COST = 0.000003
    GPT_3_COMPLETION_TOKEN_COST = 0.000004

    BASE_URL = "https://api.openai.com/v1"
    COMPLETIONS_URL = f"{BASE_URL}/chat/completions"
    IMAGE_GEN_URL = f"{BASE_URL}/images/generations"

    DEFAULT_MODEL = GPT_4
    DEFAULT_DRAW_MODEL = DALLE_3

    def __init__(self, sender: Profile = None, **kwargs):
        super(ChatGPTAPI, self).__init__(**kwargs)
        self.usage: dict = {}
        self.sender: Profile = sender

    def _get_api_key(self):
        user_key = self.sender.settings.gpt_key
        return user_key if user_key else self.API_KEY

    def _get_model(self, use_image=False):
        if use_image:
            return self.GPT_4_VISION

        settings = self.sender.settings
        user_model = settings.gpt_model
        if user_model == settings.GPT_MODEL_4:
            return self.GPT_4
        elif user_model == settings.GPT_MODEL_3_5:
            return self.GPT_3
        return self.DEFAULT_MODEL

    def _get_draw_model(self):
        return self.DEFAULT_DRAW_MODEL

    def _get_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._get_api_key()}"
        }

    def completions(self, messages: list, use_image=False) -> GPTAPIResponse:
        model = self._get_model(use_image=use_image)
        payload = {
            "model": model,
            "messages": messages
        }

        if model in [self.GPT_4, self.GPT_4_VISION]:
            prompt_token_cost = self.GPT_4_PROMPT_TOKEN_COST
            completion_token_cost = self.GPT_4_COMPLETION_TOKEN_COST
        elif model == self.GPT_3:
            prompt_token_cost = self.GPT_3_PROMPT_TOKEN_COST
            completion_token_cost = self.GPT_3_COMPLETION_TOKEN_COST
        else:
            raise RuntimeError()

        if model == self.GPT_4_VISION:
            payload['max_tokens'] = 1024

        r_json = self._do_request(self.COMPLETIONS_URL, payload)
        self.usage = r_json.get('usage')
        self.usage.update({
            'prompt_token_cost': prompt_token_cost,
            'completion_token_cost': completion_token_cost
        })

        answer = r_json['choices'][0]['message']['content']
        r = GPTAPIResponse()
        r.text = answer
        return r

    def draw(self, prompt: str) -> GPTAPIResponse:
        model = self._get_draw_model()
        if model == self.DALLE_3:
            count = 1
            size = "1792x1024"
            cost = self.DALLE_3_IMAGE_COST
        elif model == self.DALLE_2:
            count = 3
            size = "1024×1024"
            cost = self.DALLE_2_IMAGE_COST
        else:
            raise RuntimeError()

        payload = {
            "model": model,
            "prompt": prompt,
            "n": count,
            "size": size,
            "quality": "hd"
        }
        r_json = self._do_request(self.IMAGE_GEN_URL, payload)
        self.usage = {'images_tokens': count, 'image_cost': cost}
        r = GPTAPIResponse()
        r.images_url = [x['url'] for x in r_json['data']]
        r.images_prompt = r_json['data'][0]['revised_prompt']
        return r

    def _do_request(self, url, payload):
        proxies = {"https": env.str("SOCKS5_PROXY"), "http": env.str("SOCKS5_PROXY")}
        r = self.requests.post(url, headers=self._get_headers(), json=payload, proxies=proxies)
        if r.status_code != 200:
            try:
                r_json = r.json()
                r_json['payload'] = payload
            except JSONDecodeError:
                raise PWarning("Ошибка. Не получилось обработать запрос.")
        else:
            r_json = r.json()

        if error := r_json.get('error'):
            code = error.get('code')
            if code == 'content_policy_violation':
                raise PWarning("ChatGPT не может обработать запрос по политикам безопасности")
            elif code == 503:
                raise PWarning("ChatGPT недоступен")
            elif code == 'insufficient_quota':
                raise PWarning("Закончились деньги((")
            elif code == 'invalid_api_key':
                raise PWarning("Некорректный api key")
            raise PError("Какая-то ошибка API ChatGPT")
        return r_json

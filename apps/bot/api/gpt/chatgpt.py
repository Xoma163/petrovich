from json import JSONDecodeError

from apps.bot.api.gpt.gpt import GPT
from apps.bot.api.gpt.response import GPTAPIResponse
from apps.bot.api.handler import API
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning, PError
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.utils.proxy import get_proxies
from petrovich.settings import env


class GPTModel:
    def __init__(self, name: str, verbose_name: str = None, prompt_token_cost: float = None,
                 completion_token_cost: float = None, image_cost: float = None, voice_recognition_cost=None):
        """
        prompt_token_cost и completion_token_cost указываются для 1М tokens
        image_cost для 1 картинки
        """

        self.name = name
        self.verbose_name = verbose_name
        self.prompt_1m_token_cost: float = prompt_token_cost
        self.completion_1m_token_cost: float = completion_token_cost
        self.image_cost: float = image_cost
        self.voice_recognition_1_min_cost: float = voice_recognition_cost

    @property
    def prompt_token_cost(self):
        return self.prompt_1m_token_cost / 1000000 if self.prompt_1m_token_cost else None

    @property
    def completion_token_cost(self):
        return self.completion_1m_token_cost / 1000000 if self.completion_1m_token_cost else None

    @property
    def voice_recognition_cost(self):
        return self.voice_recognition_1_min_cost / 60 if self.voice_recognition_1_min_cost else None

    def __eq__(self, other) -> bool:
        return self.name == other.name


class GPTModels:
    # GPT-4 Turbo
    GPT_4_TURBO = GPTModel("gpt-4-turbo-2024-04-09", "GPT-4 TURBO", 10, 30)

    # GPT-4
    GPT_4 = GPTModel("gpt-4", "GPT-4", 30, 60)
    GPT_4_32K = GPTModel("gpt-4-32k", "GPT-4 32K", 60, 120)

    # GPT-3.5 Turbo
    GPT_3_5_TURBO_0125 = GPTModel("gpt-3.5-turbo-0125", "GPT-3.5 TURBO 0125", 0.5, 1.5)

    # image models
    DALLE_3 = GPTModel("dall-e-3", "DALLE 3", image_cost=0.120)
    DALLE_2 = GPTModel("dall-e-2", "DALLE 2", image_cost=0.2)

    # Audio models
    WHISPER = GPTModel("whisper-1", voice_recognition_cost=0.006)

    # older models
    GPT_4_0125 = GPTModel("gpt-4-0125-preview", "GPT-4 0125", 10, 30)
    GPT_4_1106 = GPTModel("gpt-4-1106-preview", "GPT-4 1106", 10, 30)
    GPT_3_5_TURBO_1106 = GPTModel("gpt-3.5-turbo-1106", "GPT-3.5 TURBO 1106", 1, 2)
    GPT_3_5_TURBO_0613 = GPTModel("gpt-3.5-turbo-0613", "GPT-3.5 TURBO 0613", 1.5, 2)
    GPT_3_5_TURBO_16K_0613 = GPTModel("gpt-3.5-turbo-16k-0613", "GPT-3.5 TURBO 16K 0613", 3, 4)
    GPT_3_5_TURBO_0301 = GPTModel("gpt-3.5-turbo-0301", "GPT-3.5 TURBO 16K 0613", 1.5, 2)

    @classmethod
    def get_all_models(cls) -> list:
        return [cls.__dict__[x] for x in cls.__dict__ if isinstance(cls.__dict__[x], GPTModel)]

    @classmethod
    def get_completions_models(cls) -> list:
        return [cls.GPT_4_TURBO, cls.GPT_4, cls.GPT_4_32K, cls.GPT_3_5_TURBO_0125, cls.GPT_4_0125, cls.GPT_4_1106,
                cls.GPT_3_5_TURBO_1106, cls.GPT_3_5_TURBO_0613, cls.GPT_3_5_TURBO_16K_0613, cls.GPT_3_5_TURBO_0301]

    @classmethod
    def get_image_models(cls) -> list:
        return [cls.DALLE_3, cls.DALLE_2]

    @classmethod
    def get_model_by_name(cls, name) -> GPTModel:
        models = cls.get_all_models()
        for model in models:
            if model.name == name:
                return model
        raise ValueError


class ChatGPTAPI(GPT, API):
    API_KEY = env.str("OPENAI_KEY")

    BASE_URL = "https://api.openai.com/v1"
    COMPLETIONS_URL = f"{BASE_URL}/chat/completions"
    IMAGE_GEN_URL = f"{BASE_URL}/images/generations"
    VOICE_RECOGNITION_URL = f"{BASE_URL}/audio/transcriptions"

    DEFAULT_MODEL = GPTModels.GPT_4_TURBO
    DEFAULT_DRAW_MODEL = GPTModels.DALLE_3
    DEFAULT_VISION_MODEL = GPTModels.GPT_4_TURBO
    DEFAULT_VOICE_RECOGNITION_MODEL = GPTModels.WHISPER

    GPT_4_VISION_MAX_TOKENS = 1024

    def __init__(self, sender: "Profile" = None, **kwargs):
        super(ChatGPTAPI, self).__init__(**kwargs)
        self.usage: dict = {}
        self.sender: "Profile" = sender

    def _get_api_key(self) -> str:
        user_key = self.sender.settings.gpt_key
        if user_key:
            return user_key
        if self.sender.check_role(Role.TRUSTED):
            return self.API_KEY
        raise PWarning("Нет доступа")

    def _get_model(self, use_image=False) -> GPTModel:
        if use_image:
            return self.DEFAULT_VISION_MODEL

        from apps.bot.models import UserSettings
        settings: UserSettings = self.sender.settings
        try:
            return settings.get_gpt_model()
        except ValueError:
            return self.DEFAULT_MODEL

    def _get_draw_model(self):
        return self.DEFAULT_DRAW_MODEL

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self._get_api_key()}"
        }

    def completions(self, messages: list, use_image=False) -> GPTAPIResponse:
        model = self._get_model(use_image=use_image)
        payload = {
            "model": model.name,
            "messages": messages
        }

        if use_image:
            payload['max_tokens'] = self.GPT_4_VISION_MAX_TOKENS

        r_json = self._do_request(self.COMPLETIONS_URL, json=payload)
        self.usage = r_json.get('usage')
        self.usage.update({
            'prompt_token_cost': model.prompt_token_cost,
            'completion_token_cost': model.completion_token_cost
        })

        answer = r_json['choices'][0]['message']['content']
        r = GPTAPIResponse()
        r.text = answer
        return r

    def draw(self, prompt: str) -> GPTAPIResponse:
        model = self._get_draw_model()
        if model == GPTModels.DALLE_3:
            count = 1
            size = "1792x1024"
        elif model == GPTModels.DALLE_2:
            count = 3
            size = "1024×1024"
        else:
            raise RuntimeError()

        payload = {
            "model": model,
            "prompt": prompt,
            "n": count,
            "size": size,
            "quality": "hd"
        }
        r_json = self._do_request(self.IMAGE_GEN_URL, json=payload)
        self.usage = {'images_tokens': count, 'image_cost': model.image_cost}
        r = GPTAPIResponse()
        r.images_url = [x['url'] for x in r_json['data']]
        r.images_prompt = r_json['data'][0]['revised_prompt']
        return r

    def recognize_voice(self, audio: AudioAttachment) -> str:
        model = self.DEFAULT_VOICE_RECOGNITION_MODEL
        data = {
            "model": model.name
        }
        r_json = self._do_request(self.VOICE_RECOGNITION_URL, data=data, files={'file': audio.content})
        self.usage = {
            'duration': audio.duration,
            'voice_recognition_cost': model.voice_recognition_cost
        }

        answer = r_json['text']
        return answer

    def _do_request(self, url, **kwargs):
        r = self.requests.post(url, headers=self._get_headers(), proxies=get_proxies(), **kwargs)
        if r.status_code != 200:
            try:
                r_json = r.json()
            except JSONDecodeError as e:
                raise PWarning("Ошибка. Не получилось обработать запрос.") from e
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
                raise PWarning("Некорректный API KEY. Проверьте свой ключ")
            raise PError("Какая-то ошибка API ChatGPT")
        return r_json

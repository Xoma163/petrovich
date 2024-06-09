import re
from json import JSONDecodeError

from apps.bot.api.gpt.gpt import GPTAPI
from apps.bot.api.gpt.message import GPTMessages
from apps.bot.api.gpt.models import GPTModels, GPTCompletionModel, GPTImageDrawModel, GPTVoiceRecognitionModel
from apps.bot.api.gpt.response import GPTAPICompletionsResponse, GPTAPIImageDrawResponse, GPTAPIVoiceRecognitionResponse
from apps.bot.api.gpt.usage import GPTAPIImageDrawUsage, GPTAPIVoiceRecognitionUsage, GPTAPICompletionsUsage
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning, PError
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.utils.proxy import get_proxies
from petrovich.settings import env


class ChatGPTAPI(GPTAPI):
    API_KEY = env.str("OPENAI_KEY")

    BASE_URL: str = "https://api.openai.com/v1"
    COMPLETIONS_URL: str = f"{BASE_URL}/chat/completions"
    IMAGE_GEN_URL: str = f"{BASE_URL}/images/generations"
    VOICE_RECOGNITION_URL: str = f"{BASE_URL}/audio/transcriptions"

    DEFAULT_COMPLETIONS_MODEL: GPTCompletionModel = GPTModels.GPT_4_OMNI
    DEFAULT_DRAW_MODEL: GPTImageDrawModel = GPTModels.DALLE_3
    DEFAULT_VISION_MODEL: GPTCompletionModel = GPTModels.GPT_4_OMNI
    DEFAULT_VOICE_RECOGNITION_MODEL: GPTVoiceRecognitionModel = GPTModels.WHISPER

    GPT_4_VISION_MAX_TOKENS = 1024

    ERRORS_MAP = {
        'content_policy_violation': "ChatGPT не может обработать запрос по политикам безопасности",
        503: "ChatGPT недоступен",
        'insufficient_quota': "Закончились деньги((",
        'invalid_api_key': "Некорректный API KEY. Проверьте свой ключ",
        'rate_limit_exceeded': "Слишком большой запрос"
    }

    def __init__(self, sender=None, **kwargs):
        super(ChatGPTAPI, self).__init__(**kwargs)
        self.sender = sender

    def completions(self, messages: GPTMessages, use_image=False) -> GPTAPICompletionsResponse:
        model = self._get_model(use_image=use_image)
        payload = {
            "model": model.name,
            "messages": messages.get_messages()
        }

        if use_image:
            payload['max_tokens'] = self.GPT_4_VISION_MAX_TOKENS

        r_json = self._do_request(self.COMPLETIONS_URL, json=payload)
        usage_dict = r_json.get('usage')
        usage = GPTAPICompletionsUsage(
            model=model,
            completion_tokens=usage_dict['completion_tokens'],
            prompt_tokens=usage_dict['prompt_tokens']
        )

        answer = r_json['choices'][0]['message']['content']
        r = GPTAPICompletionsResponse(
            text=answer,
            usage=usage
        )
        return r

    def draw(self, prompt: str) -> GPTAPIImageDrawResponse:
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
            "model": model.name,
            "prompt": prompt,
            "n": count,
            "size": size,
            "quality": "hd"
        }
        r_json = self._do_request(self.IMAGE_GEN_URL, json=payload)

        usage = GPTAPIImageDrawUsage(
            model=model,
            images_count=count,
        )

        r = GPTAPIImageDrawResponse(
            usage=usage,
            images_url=[x['url'] for x in r_json['data']],
            images_prompt=r_json['data'][0]['revised_prompt']
        )
        return r

    def recognize_voice(self, audio: AudioAttachment) -> GPTAPIVoiceRecognitionResponse:
        model = self.DEFAULT_VOICE_RECOGNITION_MODEL
        data = {
            "model": model.name,
            "response_format": "verbose_json",
        }

        file = (f"audio.{audio.ext}", audio.download_content())
        r_json = self._do_request(self.VOICE_RECOGNITION_URL, data=data, files={'file': file})

        usage = GPTAPIVoiceRecognitionUsage(
            model=model,
            voice_duration=r_json['duration']
        )

        r = GPTAPIVoiceRecognitionResponse(
            text=r_json['text'],
            usage=usage
        )
        return r

    def _do_request(self, url, **kwargs):
        r = self.requests.post(url, headers=self._headers, proxies=get_proxies(), **kwargs)
        if r.status_code != 200:
            try:
                r_json = r.json()
            except JSONDecodeError as e:
                raise PWarning("Ошибка. Не получилось обработать запрос.") from e
        else:
            r_json = r.json()

        if error := r_json.get('error'):
            code = error.get('code')
            error_str = self.ERRORS_MAP.get(code, "Какая-то ошибка API ChatGPT")

            if code == "rate_limit_exceeded":
                message = error.get('message')
                _r = re.compile(r'Limit (\d*), Requested (\d+)Visit (.*) to').findall(message)
                if _r:
                    _r = _r[0]
                    error_str += f"\nЗапрошено токенов - {_r[1]}, доступно - {_r[0]}. Подробнее - {_r[2]}"

            raise PError(error_str)

        return r_json

    def _get_api_key(self) -> str:
        user_key = self.sender.settings.chat_gpt_key
        if user_key:
            return user_key
        if self.sender.check_role(Role.TRUSTED):
            return self.API_KEY
        raise PWarning("Нет доступа")

    def _get_model(self, use_image=False) -> GPTCompletionModel:
        if use_image:
            return self.DEFAULT_VISION_MODEL

        from apps.bot.models import UserSettings
        settings: UserSettings = self.sender.settings
        try:
            return settings.get_gpt_model()
        except ValueError:
            return self.DEFAULT_COMPLETIONS_MODEL

    def _get_draw_model(self):
        return self.DEFAULT_DRAW_MODEL

    @property
    def _headers(self):
        return {
            "Authorization": f"Bearer {self._get_api_key()}"
        }

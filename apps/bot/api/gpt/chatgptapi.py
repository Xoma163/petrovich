import concurrent
import re
from concurrent.futures import ThreadPoolExecutor
from json import JSONDecodeError
from ssl import SSLError

from apps.bot.api.gpt.gpt import GPTAPI
from apps.bot.api.gpt.message import GPTMessages, GPTMessageRole
from apps.bot.api.gpt.models import GPTModels, GPTCompletionModel, GPTImageDrawModel, GPTVoiceRecognitionModel, \
    GPTImageFormat, GPTImageQuality
from apps.bot.api.gpt.response import GPTAPICompletionsResponse, GPTAPIImageDrawResponse, GPTAPIVoiceRecognitionResponse
from apps.bot.api.gpt.usage import GPTAPIImageDrawUsage, GPTAPIVoiceRecognitionUsage, GPTAPICompletionsUsage
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning, PError
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.utils.proxy import get_proxies
from apps.bot.utils.utils import retry
from petrovich.settings import env


class ChatGPTAPI(GPTAPI):
    API_KEY = env.str("OPENAI_KEY")

    BASE_URL: str = "https://api.openai.com/v1"
    COMPLETIONS_URL: str = f"{BASE_URL}/chat/completions"
    IMAGE_GEN_URL: str = f"{BASE_URL}/images/generations"
    VOICE_RECOGNITION_URL: str = f"{BASE_URL}/audio/transcriptions"

    DEFAULT_COMPLETIONS_MODEL: GPTCompletionModel = GPTModels.GPT_4_O
    DEFAULT_DRAW_MODEL: GPTImageDrawModel = GPTModels.DALLE_3_ALBUM
    DEFAULT_VISION_MODEL: GPTCompletionModel = GPTModels.GPT_4_O
    DEFAULT_VOICE_RECOGNITION_MODEL: GPTVoiceRecognitionModel = GPTModels.WHISPER

    GPT_4_VISION_MAX_TOKENS = 1024

    ERRORS_MAP = {
        'content_policy_violation': "ChatGPT не может обработать запрос по политикам безопасности",
        503: "ChatGPT недоступен",
        'insufficient_quota': "Закончились деньги((",
        'invalid_api_key': "Некорректный API KEY. Проверьте свой ключ",
        'rate_limit_exceeded': "Слишком большой запрос",
        'model_not_found': "Модель не существует или у вас нет к ней доступа"
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

        # ToDo: костыль, так как o1 не умеют в system role
        if model in [GPTModels.O1, GPTModels.O1_MINI, GPTModels.O3_MINI]:
            if payload['messages'][0]['role'] == GPTMessageRole.SYSTEM:
                payload['messages'][0]['role'] = GPTMessageRole.USER

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

    def _fetch_image(self, payload) -> (str, str):
        r_json = self._do_request(self.IMAGE_GEN_URL, json=payload)
        image_data = r_json['data'][0]
        return image_data['url'], image_data['revised_prompt']

    def draw(
            self,
            prompt: str,
            image_format: GPTImageFormat,
            quality: GPTImageQuality,
            count: int = 1,
    ) -> GPTAPIImageDrawResponse:
        model = self._get_draw_model(image_format, quality)

        size = f"{model.width}x{model.height}"

        payload = {
            "model": model.name,
            "prompt": prompt,
            "n": 1,  # max restriction by api
            "size": size,
        }
        if quality:
            payload["quality"] = quality

        usage = GPTAPIImageDrawUsage(
            model=model,
            images_count=count,
        )
        r = GPTAPIImageDrawResponse(
            usage=usage,
            images_url=[],
            images_prompt=""
        )
        if count > 1:
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(self._fetch_image, payload) for _ in range(count)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            r.images_url = [url for url, _ in results]
            r.images_prompt = results[0][1]
        else:
            url, prompt = self._fetch_image(payload)
            r.images_url = [url]
            r.images_prompt = prompt
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

    @retry(3, SSLError, sleep_time=2)
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

        from apps.bot.models import ProfileSettings
        settings: ProfileSettings = self.sender.settings
        try:
            return settings.get_gpt_model()
        except ValueError:
            return self.DEFAULT_COMPLETIONS_MODEL

    @staticmethod
    def _get_draw_model(gpt_image_format: GPTImageFormat, quality: GPTImageQuality):
        """
        Получение модели для рисования. Стандартная модель - SQUARE STANDARD
        """
        models_map = {
            (GPTImageFormat.PORTAIR, GPTImageQuality.HIGH): GPTModels.DALLE_3_PORTAIR_HD,
            (GPTImageFormat.PORTAIR, GPTImageQuality.STANDARD): GPTModels.DALLE_3_PORTAIR,
            (GPTImageFormat.SQUARE, GPTImageQuality.HIGH): GPTModels.DALLE_3_SQUARE_HD,
            (GPTImageFormat.SQUARE, GPTImageQuality.STANDARD): GPTModels.DALLE_3_SQUARE,
            (GPTImageFormat.ALBUM, GPTImageQuality.HIGH): GPTModels.DALLE_3_ALBUM_HD,
            (GPTImageFormat.ALBUM, GPTImageQuality.STANDARD): GPTModels.DALLE_3_ALBUM
        }
        return models_map.get((gpt_image_format, quality), GPTModels.DALLE_3_SQUARE)

    @property
    def _headers(self):
        return {
            "Authorization": f"Bearer {self._get_api_key()}"
        }

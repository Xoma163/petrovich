from abc import abstractmethod

from apps.bot.api.handler import API
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.gpt.api.responses import (
    GPTCompletionsResponse,
    GPTImageDrawResponse,
    GPTVisionResponse,
    GPTVoiceRecognitionResponse
)
from apps.gpt.enums import GPTImageFormat, GPTImageQuality
from apps.gpt.gpt_models.base import (
    GPTCompletionModel,
    GPTImageDrawModel,
    GPTVisionModel,
    GPTVoiceRecognitionModel, GPTModels
)
from apps.gpt.messages.base import GPTMessages
from petrovich.settings import env


class GPTAPI(API):
    def __init__(self, sender=None, *args, **kwargs):
        super(GPTAPI, self).__init__(*args, **kwargs)
        self.sender = sender

    @property
    @abstractmethod
    def base_url(self) -> str:
        """
        Хост, куда будут делаться запросы API
        """
        pass

    @property
    def api_key(self) -> str:
        """
        Получение ключа, если он проставлен пользователем, иначе общий ключ, если есть доступ, иначе ошибка
        """
        if gpt_settings := getattr(self.sender, "gpt_settings", None):
            user_key = getattr(gpt_settings, self.gpt_settings_key_field)
            if user_key:
                return user_key
        if self.sender.check_role(Role.GPT):
            return env.str(self.api_key_env_name)
        raise PWarning("Нет доступа")

    @property
    @abstractmethod
    def api_key_env_name(self) -> str:
        """
        Имя переменной среды, в которой содержится базовый API KEY
        """
        pass

    @property
    @abstractmethod
    def gpt_settings_key_field(self) -> str:
        """
        Имя поля в котором хранится ключ пользователя
        """
        pass

    @property
    @abstractmethod
    def gpt_settings_model_field(self) -> str:
        """
        Имя поля в котором хранится выбранная пользователем модель
        """
        pass

    @property
    @abstractmethod
    def models(self) -> type[GPTModels]:
        """
        Список всех моделей
        """
        pass

    # @abstractmethod
    # def do_request(self, url, **kwargs) -> dict:
    #     """
    #     Выполнение любого запроса.
    #     Должно выполняться через self.request. ...
    #     """
    #     pass


class CompletionsMixin:
    @property
    @abstractmethod
    def completions_url(self) -> str:
        pass

    @property
    @abstractmethod
    def default_completions_model(self) -> GPTCompletionModel:
        pass

    def get_completions_model(self) -> GPTCompletionModel:
        if gpt_settings := getattr(self.sender, "gpt_settings", None):  # noqa
            if user_model_str := getattr(gpt_settings, self.gpt_settings_model_field):  # noqa
                return self.models.get_model_by_name(user_model_str, GPTCompletionModel)  # noqa

        return self.default_completions_model

    @abstractmethod
    def completions(self, messages: GPTMessages) -> GPTCompletionsResponse:
        pass


class VisionMixin:

    @property
    @abstractmethod
    def vision_url(self) -> str:
        pass

    @property
    @abstractmethod
    def default_vision_model(self) -> GPTVisionModel:
        pass

    @abstractmethod
    def get_vision_model(self) -> GPTVisionModel:
        pass

    @abstractmethod
    def vision(self, messages: GPTMessages) -> GPTVisionResponse:
        pass


class ImageDrawMixin:
    @property
    @abstractmethod
    def draw_url(self) -> str:
        pass

    @property
    @abstractmethod
    def default_draw_model(self) -> GPTImageDrawModel:
        pass

    @abstractmethod
    def get_draw_model(self, gpt_image_format: GPTImageFormat, quality: GPTImageQuality) -> GPTImageDrawModel:
        pass

    @abstractmethod
    def image_draw(
            self,
            prompt: str,
            image_format: GPTImageFormat,
            quality: GPTImageQuality,
            count: int = 1,
    ) -> GPTImageDrawResponse:
        pass


class VoiceRecognitionMixin:

    @property
    @abstractmethod
    def voice_recognition_url(self) -> str:
        pass

    @property
    @abstractmethod
    def default_voice_recognition_model(self) -> GPTVoiceRecognitionModel:
        pass

    @abstractmethod
    def get_voice_recognition_model(self) -> GPTVoiceRecognitionModel:
        pass

    @abstractmethod
    def voice_recognition(self, audio_ext: str, content: bytes) -> GPTVoiceRecognitionResponse:
        pass

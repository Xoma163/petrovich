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
from apps.gpt.messages.base import GPTMessages
from apps.gpt.models import (
    CompletionModel,
    VisionModel,
    ImageDrawModel,
    ImageEditModel,
    VoiceRecognitionModel
)
from apps.gpt.protocols import (
    HasCompletions,
    HasVision,
    HasVoiceRecognition,
    HasImageEdit,
    HasImageDraw
)
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

    @property
    def api_key(self) -> str:
        """
        Получение ключа, если он проставлен пользователем, иначе общий ключ, если есть доступ, иначе ошибка
        """
        if gpt_settings := getattr(self.sender, "gpt_settings", None):
            # ToDo:
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


class CompletionsAPIMixin(HasCompletions):
    @property
    @abstractmethod
    def completions_url(self) -> str:
        pass

    # ToDo: сделать метод для всех миксинов
    def get_completions_model(self) -> CompletionModel:
        # ToDo: поправить получение модели
        if gpt_settings := getattr(self.sender, "gpt_settings", None):  # noqa
            if user_model_str := getattr(gpt_settings, self.gpt_settings_model_field):  # noqa
                return self.models.get_model_by_name(user_model_str, GPTCompletionModel)  # noqa

        # ToDo: поправить получение стандартной модели
        return self.default_completions_model

    @abstractmethod
    def completions(self, messages: GPTMessages) -> GPTCompletionsResponse:
        pass


class VisionAPIMixin(HasVision):

    @property
    @abstractmethod
    def vision_url(self) -> str:
        pass

    @abstractmethod
    def get_vision_model(self) -> VisionModel:
        pass

    @abstractmethod
    def vision(self, messages: GPTMessages) -> GPTVisionResponse:
        pass


class ImageDrawAPIMixin(HasImageDraw):
    @property
    @abstractmethod
    def image_draw_url(self) -> str:
        pass

    @abstractmethod
    def get_image_draw_model(self, gpt_image_format: GPTImageFormat, quality: GPTImageQuality) -> ImageDrawModel:
        pass

    @abstractmethod
    def draw_image(
            self,
            prompt: str,
            image_format: GPTImageFormat,
            quality: GPTImageQuality,
            count: int = 1,
    ) -> GPTImageDrawResponse:
        pass


class ImageEditAPIMixin(HasImageEdit):
    @property
    @abstractmethod
    def image_edit_url(self) -> str:
        pass

    @abstractmethod
    def get_image_edit_model(self) -> ImageEditModel:
        pass

    @abstractmethod
    def edit_image(
            self,
            prompt: str,
            image: bytes,
            mask: bytes,
            count: int = 1
    ) -> GPTImageDrawResponse:
        pass


class VoiceRecognitionAPIMixin(HasVoiceRecognition):

    @property
    @abstractmethod
    def voice_recognition_url(self) -> str:
        pass

    @abstractmethod
    def get_voice_recognition_model(self) -> VoiceRecognitionModel:
        pass

    @abstractmethod
    def voice_recognition(self, audio_ext: str, content: bytes) -> GPTVoiceRecognitionResponse:
        pass

from abc import abstractmethod

from apps.commands.gpt.api.responses import (
    GPTCompletionsResponse,
    GPTImageDrawResponse,
    GPTVisionResponse,
    GPTVoiceRecognitionResponse
)
from apps.commands.gpt.messages.base import GPTMessages
from apps.commands.gpt.models import (
    CompletionsModel,
    VisionModel,
    ImageDrawModel,
    ImageEditModel,
    VoiceRecognitionModel
)
from apps.commands.gpt.protocols import (
    HasCompletions,
    HasVision,
    HasVoiceRecognition,
    HasImageEdit,
    HasImageDraw
)
from apps.connectors.api.handler import API


class GPTAPI(API):
    def __init__(self, api_key: str, *args, **kwargs):
        super(GPTAPI, self).__init__(*args, **kwargs)
        self.api_key: str = api_key

    @property
    @abstractmethod
    def base_url(self) -> str:
        """
        Хост, куда будут делаться запросы API
        """

    @abstractmethod
    def check_key(self) -> bool:
        pass


class CompletionsAPIMixin(HasCompletions):
    @property
    @abstractmethod
    def completions_url(self) -> str:
        pass

    @abstractmethod
    def completions(
            self,
            messages: GPTMessages,
            model: CompletionsModel,
            extra_data: dict
    ) -> GPTCompletionsResponse:
        pass


class VisionAPIMixin(HasVision):

    @property
    @abstractmethod
    def vision_url(self) -> str:
        pass

    @abstractmethod
    def vision(
            self,
            messages: GPTMessages,
            model: VisionModel,
            extra_data: dict
    ) -> GPTVisionResponse:
        pass


class ImageDrawAPIMixin(HasImageDraw):
    @property
    @abstractmethod
    def image_draw_url(self) -> str:
        pass

    @abstractmethod
    def draw_image(
            self,
            prompt: str,
            model: ImageDrawModel,
            count: int = 1,
    ) -> GPTImageDrawResponse:
        pass


class ImageEditAPIMixin(HasImageEdit):
    @property
    @abstractmethod
    def image_edit_url(self) -> str:
        pass

    @abstractmethod
    def edit_image(
            self,
            prompt: str,
            model: ImageEditModel,
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
    def voice_recognition(self, audio_ext: str, content: bytes,
                          model: VoiceRecognitionModel) -> GPTVoiceRecognitionResponse:
        pass

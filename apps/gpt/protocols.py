import logging
from typing import Protocol

from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.models import Profile, Chat
from apps.bot.protocols import CommandProtocol
from apps.gpt.api.responses import (
    GPTCompletionsResponse,
    GPTVisionResponse,
    GPTImageDrawResponse,
    GPTVoiceRecognitionResponse,
    GPTAPIResponse
)
from apps.gpt.messages.base import GPTMessages
from apps.gpt.models import (
    CompletionsModel,
    VisionModel,
    ImageDrawModel,
    ImageEditModel,
    VoiceRecognitionModel,
    Provider, GPTModel
)
from apps.gpt.models import ProfileGPTSettings

logger = logging.getLogger(__name__)


class GPTKeyProtocol(Protocol):
    def menu_key(self) -> ResponseMessageItem: ...

    def check_key(self) -> ResponseMessage | None: ...


class GPTModelChoiceProtocol(Protocol):
    def menu_models(self) -> ResponseMessageItem: ...

    def menu_model(self) -> ResponseMessageItem: ...


class GPTPrepromptProtocol(Protocol):
    def menu_preprompt(self) -> ResponseMessageItem: ...

    def get_preprompt(self, sender: Profile, chat: Chat) -> str | None: ...


class GPTStatisticsProtocol(Protocol):
    def menu_statistics(self) -> ResponseMessageItem: ...

    def add_statistics(self, api_response: GPTAPIResponse): ...


class GPTCommandProtocol(
    CommandProtocol,
    GPTKeyProtocol,
    GPTModelChoiceProtocol,
    GPTPrepromptProtocol,
    GPTStatisticsProtocol
):
    provider: "GPTProvider"  # noqa circular import
    provider_model: Provider

    def get_dialog(self, extra_message: str | None = None) -> GPTMessages: ...

    def get_completions_rmi(self, answer: str): ...

    def send_rmi(self, rmi) -> ResponseMessageItem | None: ...

    def get_profile_gpt_settings(self) -> ProfileGPTSettings: ...

    def get_api_key(self) -> str: ...

    def get_model(self, model_class: type[GPTModel], field_model_name: str): ...

    def get_user_model(self, field_model_name: str) -> GPTModel | None: ...

    def get_default_model(self, model_class: type[GPTModel]): ...

    def set_provider_model(self, model_class: type[GPTModel]): ...


class HasCompletions(Protocol):
    def completions(
            self,
            messages:
            GPTMessages,
            model: CompletionsModel
    ) -> GPTCompletionsResponse:
        ...


class HasVision(Protocol):
    def vision(
            self,
            messages: GPTMessages,
            model: VisionModel
    ) -> GPTVisionResponse:
        ...


class HasImageDraw(Protocol):
    def draw_image(
            self,
            prompt: str,
            model: ImageDrawModel,
            count: int = 1,
    ) -> GPTImageDrawResponse:
        ...


class HasImageEdit(Protocol):
    def edit_image(
            self,
            prompt: str,
            model: ImageEditModel,
            image: bytes,
            mask: bytes,
            count: int = 1
    ) -> GPTImageDrawResponse:
        ...


class HasVoiceRecognition(Protocol):
    def voice_recognition(
            self,
            audio_ext: str,
            content: bytes,
            model: VoiceRecognitionModel
    ) -> GPTVoiceRecognitionResponse:
        ...

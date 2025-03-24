from apps.bot.api.gpt.message import GPTMessages
from apps.bot.api.gpt.models import GPTCompletionModel, GPTImageDrawModel, GPTVoiceRecognitionModel, GPTImageFormat, \
    GPTImageQuality
from apps.bot.api.gpt.response import GPTAPICompletionsResponse, GPTAPIImageDrawResponse
from apps.bot.api.handler import API


class GPTAPI(API):
    DEFAULT_MODEL: GPTCompletionModel | None = None
    DEFAULT_DRAW_MODEL: GPTImageDrawModel | None = None
    DEFAULT_VISION_MODEL: GPTCompletionModel | None = None
    DEFAULT_VOICE_RECOGNITION_MODEL: GPTVoiceRecognitionModel | None = None

    def __init__(self, *args, **kwargs):
        super(GPTAPI, self).__init__(*args, **kwargs)

    def _get_model(self, use_image: bool = False):
        raise NotImplementedError

    def completions(self, messages: GPTMessages, use_image: bool = False) -> GPTAPICompletionsResponse:
        raise NotImplementedError

    @property
    def _headers(self) -> dict:
        raise NotImplementedError

    def draw(
            self,
            prompt: str,
            image_format: GPTImageFormat,
            quality: GPTImageQuality,
            count: int = 1,
    ) -> GPTAPIImageDrawResponse:
        """
        Метод для рисования GPTAPI, переопределяется не у всех наследников
        """

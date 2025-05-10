import io

from apps.gpt.api.base import (
    CompletionsAPIMixin,
    VisionAPIMixin,
    ImageDrawAPIMixin,
    VoiceRecognitionAPIMixin,
    ImageEditAPIMixin
)
from apps.gpt.api.openai_api import OpenAIAPI
from apps.gpt.api.responses import (
    GPTCompletionsResponse,
    GPTVisionResponse,
    GPTImageDrawResponse,
    GPTVoiceRecognitionResponse
)
from apps.gpt.enums import GPTImageFormat, GPTImageQuality
from apps.gpt.messages.base import GPTMessages
from apps.gpt.messages.consts import GPTMessageRole
from apps.gpt.usage import (
    GPTVoiceRecognitionUsage
)


class ChatGPTAPI(
    OpenAIAPI,
    CompletionsAPIMixin,
    VisionAPIMixin,
    ImageDrawAPIMixin,
    ImageEditAPIMixin,
    VoiceRecognitionAPIMixin
):

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}"
        }

    # ---------- base ---------- #

    base_url = "https://api.openai.com/v1"
    api_key_env_name = "OPENAI_KEY"

    # ---------- completions ---------- #
    completions_url = f"{base_url}/chat/completions"

    def completions(self, messages: GPTMessages) -> GPTCompletionsResponse:
        model = self.get_completions_model()
        payload = {
            "model": model.name,
            "messages": messages.get_messages()
        }

        # Костыль, так как некоторые модели "o" не умеют в system role
        # ToDo: как-то обыграть это тут
        if model in [ChatGPTModels.O1_MINI]:
            if payload['messages'][0]['role'] == GPTMessageRole.SYSTEM:
                payload['messages'][0]['role'] = GPTMessageRole.USER

        return self.do_completions_request(model, self.completions_url, json=payload, headers=self.headers)

    # ---------- vision ---------- #

    vision_url = completions_url


    def vision(self, messages: GPTMessages) -> GPTVisionResponse:
        model = self.get_vision_model()
        payload = {
            "model": model.name,
            "messages": messages.get_messages()
        }
        return self.do_vision_request(model, self.vision_url, json=payload, headers=self.headers)

    # ---------- image draw ---------- #

    image_draw_url = f"{base_url}/images/generations"

    # ToDo: возможно уедет в base
    def get_image_draw_model(self, gpt_image_format: GPTImageFormat, quality: GPTImageQuality) -> GPTImageDrawModel:
        models_map = {
            (GPTImageFormat.SQUARE, GPTImageQuality.STANDARD): ChatGPTImageDrawModels.DALLE_3_SQUARE_STANDART,
            (GPTImageFormat.PORTAIR, GPTImageQuality.STANDARD): ChatGPTImageDrawModels.DALLE_3_PORTAIR_STANDART,
            (GPTImageFormat.LANDSCAPE, GPTImageQuality.STANDARD): ChatGPTImageDrawModels.DALLE_3_LANDSCAPE_STANDART,
            (GPTImageFormat.SQUARE, GPTImageQuality.HIGH): ChatGPTImageDrawModels.DALLE_3_SQUARE_HD,
            (GPTImageFormat.PORTAIR, GPTImageQuality.HIGH): ChatGPTImageDrawModels.DALLE_3_PORTAIR_HD,
            (GPTImageFormat.LANDSCAPE, GPTImageQuality.HIGH): ChatGPTImageDrawModels.DALLE_3_LANDSCAPE_HD,
        }
        return models_map.get((gpt_image_format, quality), self.default_image_draw_model)

    def draw_image(
            self,
            prompt: str,
            image_format: GPTImageFormat,
            quality: GPTImageQuality,
            count: int = 1,
    ) -> GPTImageDrawResponse:
        model = self.get_image_draw_model(image_format, quality)
        payload = {
            "model": model.name,
            "prompt": prompt,
            "n": 1,  # max restriction by api
            "size": model.size,
            "response_format": "b64_json"
        }
        if quality:
            payload["quality"] = quality

        return self.do_image_request(
            model=model,
            url=self.image_draw_url,
            json=payload,
            count=count,
            headers=self.headers,
            log=False
        )

    # ---------- image edit ---------- #

    image_edit_url = f"{base_url}/images/edits"

    def edit_image(
            self,
            prompt: str,
            image: bytes,
            mask: bytes,
            count: int = 1,
    ) -> GPTImageDrawResponse:
        model = self.get_image_edit_model()
        payload = {
            "prompt": prompt,
            "model": model.name,
            "n": count,
            "response_format": "b64_json",
            # "size": model.size
        }
        files = {
            'image': ('image.png', io.BytesIO(image), 'image/png'),
            'mask': ('image.png', io.BytesIO(mask), 'image/png'),
        }
        return self.do_image_request(
            model,
            url=self.image_edit_url,
            data=payload,
            count=count,
            headers=self.headers,
            log=False,
            files=files
        )

    # ---------- voice recognition ---------- #

    MAX_AUDIO_FILE_SIZE_MB = 24

    @property
    def voice_recognition_url(self) -> str:
        return f"{self.base_url}/audio/transcriptions"

    def voice_recognition(self, audio_ext: str, content: bytes) -> GPTVoiceRecognitionResponse:
        model = self.get_voice_recognition_model()
        data = {
            "model": model.name,
            "response_format": "verbose_json",
        }

        file = (f"audio.{audio_ext}", content)
        r_json = self.do_request(self.voice_recognition_url, data=data, files={'file': file}, headers=self.headers)

        usage = GPTVoiceRecognitionUsage(
            model=model,
            voice_duration=r_json['duration']
        )

        r = GPTVoiceRecognitionResponse(
            text=r_json['text'],
            usage=usage
        )
        return r

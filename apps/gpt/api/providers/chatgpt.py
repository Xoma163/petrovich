import concurrent
from concurrent.futures import ThreadPoolExecutor

from apps.gpt.api.base import (
    GPTAPI,
    CompletionsMixin,
    VisionMixin,
    ImageDrawMixin,
    VoiceRecognitionMixin
)
from apps.gpt.api.openai_api import OpenAIAPI
from apps.gpt.api.responses import (
    GPTCompletionsResponse,
    GPTVisionResponse,
    GPTImageDrawResponse,
    GPTVoiceRecognitionResponse
)
from apps.gpt.enums import GPTImageFormat, GPTImageQuality
from apps.gpt.gpt_models.base import (
    GPTCompletionModel,
    GPTVisionModel,
    GPTImageDrawModel,
    GPTVoiceRecognitionModel
)
from apps.gpt.gpt_models.providers.chatgpt import (
    ChatGPTCompletionModels,
    ChatGPTVisionModels,
    ChatGPTImageDrawModels,
    ChatGPTVoiceRecognitionModels,
    ChatGPTModels
)
from apps.gpt.messages.base import GPTMessages
from apps.gpt.messages.consts import GPTMessageRole
from apps.gpt.usage import (
    GPTImageDrawUsage,
    GPTVoiceRecognitionUsage
)


class ChatGPTAPI(
    GPTAPI,
    OpenAIAPI,
    CompletionsMixin,
    VisionMixin,
    ImageDrawMixin,
    VoiceRecognitionMixin
):

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}"
        }

    # ---------- base ---------- #

    base_url = "https://api.openai.com/v1"
    api_key_env_name = "OPENAI_KEY"
    gpt_settings_key_field = "chat_gpt_key"
    gpt_settings_model_field = "chat_gpt_model"
    models = ChatGPTModels

    # ---------- completions ---------- #

    @property
    def completions_url(self) -> str:
        return f"{self.base_url}/chat/completions"

    default_completions_model: GPTCompletionModel = ChatGPTCompletionModels.O4_MINI

    def completions(self, messages: GPTMessages) -> GPTCompletionsResponse:
        model = self.get_completions_model()
        payload = {
            "model": model.name,
            "messages": messages.get_messages()
        }

        # Костыль, так как некоторые модели "o" не умеют в system role
        if model in [ChatGPTModels.O1_MINI]:
            if payload['messages'][0]['role'] == GPTMessageRole.SYSTEM:
                payload['messages'][0]['role'] = GPTMessageRole.USER

        return self.do_completions_request(model, self.completions_url, json=payload, headers=self.headers)

    # ---------- vision ---------- #

    @property
    def vision_url(self) -> str:
        return self.completions_url

    default_vision_model: GPTVisionModel = ChatGPTVisionModels.GPT_4_O

    def get_vision_model(self) -> GPTVisionModel:
        return self.default_vision_model

    def vision(self, messages: GPTMessages) -> GPTVisionResponse:
        model = self.get_vision_model()
        payload = {
            "model": model.name,
            "messages": messages.get_messages()
        }
        return self.do_vision_request(model, self.vision_url, json=payload, headers=self.headers)

    # ---------- image draw ---------- #

    @property
    def draw_url(self) -> str:
        return f"{self.base_url}/images/generations"

    default_draw_model: GPTImageDrawModel = ChatGPTImageDrawModels.DALLE_3_SQUARE

    def get_draw_model(self, gpt_image_format: GPTImageFormat, quality: GPTImageQuality) -> GPTImageDrawModel:
        models_map = {
            (GPTImageFormat.PORTAIR, GPTImageQuality.HIGH): ChatGPTImageDrawModels.DALLE_3_PORTAIR_HD,
            (GPTImageFormat.PORTAIR, GPTImageQuality.STANDARD): ChatGPTImageDrawModels.DALLE_3_PORTAIR,
            (GPTImageFormat.SQUARE, GPTImageQuality.HIGH): ChatGPTImageDrawModels.DALLE_3_SQUARE_HD,
            (GPTImageFormat.SQUARE, GPTImageQuality.STANDARD): ChatGPTImageDrawModels.DALLE_3_SQUARE,
            (GPTImageFormat.ALBUM, GPTImageQuality.HIGH): ChatGPTImageDrawModels.DALLE_3_ALBUM_HD,
            (GPTImageFormat.ALBUM, GPTImageQuality.STANDARD): ChatGPTImageDrawModels.DALLE_3_ALBUM
        }
        return models_map.get((gpt_image_format, quality), self.default_draw_model)

    def _fetch_image(self, payload) -> (str, str):
        r_json = self.do_request(self.draw_url, json=payload)
        image_data = r_json['data'][0]
        return image_data['url'], image_data['revised_prompt']

    def image_draw(
            self,
            prompt: str,
            image_format: GPTImageFormat,
            quality: GPTImageQuality,
            count: int = 1,
    ) -> GPTImageDrawResponse:
        model = self.get_draw_model(image_format, quality)

        size = f"{model.width}x{model.height}"

        payload = {
            "model": model.name,
            "prompt": prompt,
            "n": 1,  # max restriction by api
            "size": size,
        }
        if quality:
            payload["quality"] = quality

        usage = GPTImageDrawUsage(
            model=model,
            images_count=count,
        )
        r = GPTImageDrawResponse(
            images_prompt="",
            images_url=[],
            usage=usage,
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

    # ---------- voice recognition ---------- #
    MAX_AUDIO_FILE_SIZE_MB = 24

    @property
    def voice_recognition_url(self) -> str:
        return f"{self.base_url}/audio/transcriptions"

    default_voice_recognition_model: GPTVoiceRecognitionModel = ChatGPTVoiceRecognitionModels.WHISPER

    def get_voice_recognition_model(self) -> GPTVoiceRecognitionModel:
        return self.default_voice_recognition_model

    def voice_recognition(self, audio_ext: str, content: bytes) -> GPTVoiceRecognitionResponse:
        model = self.get_voice_recognition_model()
        data = {
            "model": model.name,
            "response_format": "verbose_json",
        }

        file = (f"audio.{audio_ext}", content)
        r_json = self.do_request(self.voice_recognition_url, data=data, files={'file': file})

        usage = GPTVoiceRecognitionUsage(
            model=model,
            voice_duration=r_json['duration']
        )

        r = GPTVoiceRecognitionResponse(
            text=r_json['text'],
            usage=usage
        )
        return r

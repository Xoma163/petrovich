import io
from decimal import Decimal

from apps.commands.gpt.api.base import (
    CompletionsAPIMixin,
    VisionAPIMixin,
    ImageDrawAPIMixin,
    VoiceRecognitionAPIMixin,
    ImageEditAPIMixin
)
from apps.commands.gpt.api.openai_responses_api import OpenAIResponsesAPI
from apps.commands.gpt.api.responses import (
    GPTCompletionsResponse,
    GPTVisionResponse,
    GPTImageDrawResponse,
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
from apps.commands.gpt.usage import (
    GPTVoiceRecognitionUsage
)


class ChatGPTAPI(
    OpenAIResponsesAPI,
    CompletionsAPIMixin,
    VisionAPIMixin,
    ImageDrawAPIMixin,
    ImageEditAPIMixin,
    VoiceRecognitionAPIMixin,
):

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}"
        }

    # ---------- base ---------- #

    base_url = "https://api.openai.com/v1"

    def check_key(self) -> bool:
        return self._check_key("gpt-5-nano", self.headers)

    # ---------- completions ---------- #

    completions_url = f"{base_url}/responses"

    def completions(self, messages: GPTMessages, model: CompletionsModel, extra_data: dict) -> GPTCompletionsResponse:
        payload: dict = {
            "model": model.name,
        }
        preprompt, messages_dict = messages.get_preprompt_and_messages()
        if preprompt:
            payload["instructions"] = preprompt
        payload["input"] = messages_dict

        if model.name in ['gpt-5', 'gpt-5-mini', 'gpt-5-nano'] and extra_data:
            if verbosity_level := extra_data.get('verbosity_level'):
                payload['text'] = {"verbosity": verbosity_level}
            if effort_level := extra_data.get('effort_level'):
                payload['reasoning'] = {"effort": effort_level}
            if extra_data.get("web_search"):
                payload["tools"] = [{"type": "web_search_preview"}]

        return self.do_completions_request(model, self.completions_url, json=payload, headers=self.headers)  # noqa

    # ---------- vision ---------- #

    vision_url = completions_url

    def vision(self, messages: GPTMessages, model: VisionModel, extra_data: dict) -> GPTVisionResponse:
        payload: dict = {
            "model": model.name
        }
        preprompt, messages_dict = messages.get_preprompt_and_messages()
        if preprompt:
            payload["instructions"] = preprompt
        payload["input"] = messages_dict

        if model.name in ['gpt-5', 'gpt-5-mini', 'gpt-5-nano'] and extra_data:
            if verbosity_level := extra_data['verbosity_level']:
                payload['text'] = {"verbosity": verbosity_level}
            if effort_level := extra_data['effort_level']:
                payload['reasoning'] = {"effort": effort_level}

        return self.do_vision_request(model, self.vision_url, json=payload, headers=self.headers)  # noqa

    # ---------- image draw ---------- #

    image_draw_url = f"{base_url}/images/generations"

    def draw_image(
            self,
            prompt: str,
            model: ImageDrawModel,
            count: int = 1,
    ) -> GPTImageDrawResponse:
        payload = {
            "model": model.name,
            "prompt": prompt,
            "n": 1,  # max restriction by api
            "size": model.size,
            "response_format": "b64_json",
            "quality": model.quality,
        }

        return self.do_image_request(
            model=model,  # noqa
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
            model: ImageEditModel,
            image: bytes,
            mask: bytes,
            count: int = 1,
    ) -> GPTImageDrawResponse:
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
            model,  # noqa
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

    def voice_recognition(
            self,
            audio_ext: str,
            content: bytes,
            model: type[VoiceRecognitionModel]
    ) -> GPTVoiceRecognitionResponse:
        data = {
            "model": model.name,
            "response_format": "verbose_json",
        }

        file = (f"audio.{audio_ext}", content)
        r_json = self.do_request(self.voice_recognition_url, data=data, files={'file': file}, headers=self.headers)

        usage = GPTVoiceRecognitionUsage(
            model=model,  # noqa
            voice_duration=Decimal(round(r_json['duration']))
        )

        r = GPTVoiceRecognitionResponse(
            text=r_json['text'],
            usage=usage
        )
        return r

from apps.gpt.api.base import CompletionsAPIMixin, VisionAPIMixin, ImageDrawAPIMixin
from apps.gpt.api.openai_api import OpenAIAPI
from apps.gpt.api.responses import GPTVisionResponse, GPTImageDrawResponse, GPTCompletionsResponse
from apps.gpt.messages.base import GPTMessages
from apps.gpt.models import (
    CompletionsModel,
    VisionModel,
    ImageDrawModel
)


class GrokAPI(
    OpenAIAPI,
    CompletionsAPIMixin,
    VisionAPIMixin,
    ImageDrawAPIMixin,
):
    @property
    def headers(self) -> dict:
        return {
            'Authorization': f"Bearer {self.api_key}"
        }

    # ---------- base ---------- #

    base_url = "https://api.x.ai/v1"

    def check_key(self) -> bool:
        return self._check_key("grok-3-mini", self.headers)

    # ---------- completions ---------- #

    completions_url = f"{base_url}/chat/completions"

    def completions(self, messages: GPTMessages, model: CompletionsModel) -> GPTCompletionsResponse:
        payload = {
            "model": model.name,
            "messages": messages.get_messages()
        }

        return self.do_completions_request(model, self.completions_url, json=payload, headers=self.headers),  # noqa

    # ---------- vision ---------- #

    vision_url = f"{base_url}/chat/completions"

    def vision(self, messages: GPTMessages, model: VisionModel) -> GPTVisionResponse:
        payload = {
            "model": model.name,
            "messages": messages.get_messages()
        }
        return self.do_vision_request(model, self.vision_url, json=payload, headers=self.headers),  # noqa

    # ---------- image draw ---------- #

    image_draw_url = f"{base_url}/images/generations"

    def draw_image(
            self,
            prompt: str,
            model: ImageDrawModel,
            count: int = 1,  # quality are not supported by xAI API at the moment.

    ) -> GPTImageDrawResponse:
        payload = {
            'model': model.name,
            'prompt': prompt,
            'n': count,
            # 'size': model.size # size are not supported by xAI API at the moment.
            'response_format': 'b64_json',
        }
        return self.do_image_request(
            model=model,  # noqa
            url=self.image_draw_url,
            json=payload,
            count=count,
            headers=self.headers,
            log=False
        )

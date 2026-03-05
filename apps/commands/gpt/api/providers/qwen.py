from apps.commands.gpt.api.base import CompletionsAPIMixin, VisionAPIMixin
from apps.commands.gpt.api.openai_api import OpenAIAPI
from apps.commands.gpt.api.responses import GPTCompletionsResponse, GPTVisionResponse
from apps.commands.gpt.messages.base import GPTMessages
from apps.commands.gpt.models import (
    CompletionsModel, VisionModel
)


class QwenAPI(
    OpenAIAPI,
    CompletionsAPIMixin,
    VisionAPIMixin,
):
    @property
    def headers(self) -> dict:
        return {}

    # ---------- base ---------- #

    # base_url = "http://192.168.1.10:21001"
    base_url = "http://192.168.1.20:21001"

    def check_key(self) -> bool:
        return True

    # ---------- completions ---------- #

    completions_url = f"{base_url}/chat/completions"

    def completions(self, messages: GPTMessages, model: CompletionsModel, extra_data: dict) -> GPTCompletionsResponse:
        payload = {
            "model": model.name,
            "messages": messages.get_messages()
        }

        return self.do_completions_request(model, self.completions_url, json=payload, headers=self.headers)  # noqa

    # ---------- vision ---------- #

    vision_url = f"{base_url}/chat/completions"

    def vision(self, messages: GPTMessages, model: VisionModel, extra_data: dict) -> GPTVisionResponse:
        payload = {
            "model": model.name,
            "messages": messages.get_messages()
        }
        return self.do_vision_request(model, self.vision_url, json=payload, headers=self.headers)  # noqa

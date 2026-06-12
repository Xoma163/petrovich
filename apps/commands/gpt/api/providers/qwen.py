from typing import Callable

from apps.commands.gpt.api.base import CompletionsAPIMixin, VisionAPIMixin
from apps.commands.gpt.api.openai_api import OpenAIAPI
from apps.commands.gpt.api.responses import GPTCompletionsResponse, GPTVisionResponse
from apps.commands.gpt.messages.base import GPTMessages
from apps.commands.gpt.models import CompletionsModel, VisionModel
from apps.shared.exceptions import PWarning
from petrovich.settings import env


class QwenAPI(
    OpenAIAPI,
    CompletionsAPIMixin,
    VisionAPIMixin,
):
    @property
    def headers(self) -> dict:
        return {}

    # ---------- base ---------- #
    base_url = None

    def set_base_url(self):
        variants = env.list("QWEN_API_BASE_URLS")

        import requests

        for variant in variants:
            variant = variant.rstrip("/")
            try:
                r = requests.get(f"{variant}/models", timeout=2)
                r.raise_for_status()
                self.base_url = variant
                self.completions_url = f"{variant}/chat/completions"
                self.vision_url = f"{variant}/chat/completions"
                return
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                continue
        raise PWarning("На данный момент нет работающих моделей")

    def check_key(self) -> bool:
        return True

    # ---------- completions ---------- #

    completions_url = f"{base_url}/chat/completions"

    def completions(
        self,
        messages: GPTMessages,
        model: CompletionsModel,
        extra_data: dict,
        callback_func: Callable | None = None,
    ) -> GPTCompletionsResponse:
        payload = {"model": model.name, "messages": messages.get_messages()}
        if callback_func:
            payload["stream"] = True
            payload["stream_options"] = {"include_usage": True}

        self.set_base_url()
        return self.do_completions_request(
            model,
            self.completions_url,
            json=payload,
            headers=self.headers,
            stream=True if callback_func else False,
            callback_func=callback_func,
        )  # noqa

    # ---------- vision ---------- #

    vision_url = f"{base_url}/chat/completions"

    def vision(
        self,
        messages: GPTMessages,
        model: VisionModel,
        extra_data: dict,
        callback_func: Callable | None = None,
    ) -> GPTVisionResponse:
        payload = {"model": model.name, "messages": messages.get_messages()}
        if callback_func:
            payload["stream"] = True
            payload["stream_options"] = {"include_usage": True}

        self.set_base_url()
        # Хардкод
        if self.base_url == "http://192.168.1.10:11031":
            raise PWarning("Не работает")

        return self.do_vision_request(
            model,
            self.vision_url,
            json=payload,
            headers=self.headers,
            stream=True if callback_func else False,
            callback_func=callback_func,
        )  # noqa

import logging
from typing import Callable

import requests

from apps.commands.gpt.api.base import GPTAPI, CompletionsAPIMixin
from apps.commands.gpt.api.responses import GPTCompletionsResponse
from apps.commands.gpt.messages.base import GPTMessages
from apps.commands.gpt.models import CompletionsModel
from apps.commands.gpt.usage import GPTCompletionsUsage
from apps.shared.exceptions import PWarning
from petrovich.settings import env

logger = logging.getLogger(__name__)


class HermesAPI(GPTAPI, CompletionsAPIMixin):
    IMAGE_INSTRUCTION = (
        "When the user requests an image, picture, illustration, or drawing, use the image_generate tool "
        "and include the generated image in your final response using the platform's media convention. "
        "Do not substitute ASCII art, an image description, or an invented image URL for a generated image "
        "unless the user explicitly requests text art. If image generation fails, say so plainly."
    )

    @property
    def base_url(self) -> str:
        return env.str("HERMES_API_BASE_URL", default="").rstrip("/")

    @property
    def completions_url(self) -> str:
        return f"{self.base_url}/chat/completions"

    def check_key(self) -> bool:
        return bool(self.api_key)

    def completions(
        self,
        messages: GPTMessages,
        model: CompletionsModel,
        extra_data: dict,
        callback_func: Callable | None = None,
    ) -> GPTCompletionsResponse:
        if not self.base_url or not self.api_key:
            raise PWarning("Hermes не настроен: укажите HERMES_API_BASE_URL и HERMES_API_KEY")

        try:
            response = requests.post(
                self.completions_url,
                json={
                    "model": model.name,
                    "messages": [
                        {"role": "system", "content": self.IMAGE_INSTRUCTION},
                        *messages.get_messages(),
                    ],
                    "stream": False,
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=(5, 300),
            )
            response.raise_for_status()
            data = response.json()
            choice = data["choices"][0]
            if choice.get("finish_reason") == "error" or data.get("hermes", {}).get("failed"):
                raise ValueError("Hermes agent failed")
            text = choice["message"]["content"]
            if not isinstance(text, str):
                raise ValueError("Hermes returned no text")
        except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
            logger.warning("Hermes API request failed: %s", type(exc).__name__)
            raise PWarning("Hermes недоступен или не смог обработать запрос") from exc

        usage = data.get("usage") or {}
        return GPTCompletionsResponse(
            text=text,
            usage=GPTCompletionsUsage(
                model=model,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
            ),
            raw_response_output=None,
        )

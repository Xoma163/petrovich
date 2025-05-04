from abc import ABC
from dataclasses import dataclass

from apps.gpt.usage import GPTImageDrawUsage, GPTCompletionsUsage, GPTVisionUsage, GPTVoiceRecognitionUsage, \
    GPTCompletionsVisionUsage


class GPTAPIResponse(ABC):
    pass


@dataclass
class GPTCompletionsVisionResponse(GPTAPIResponse):
    text: str
    usage: GPTCompletionsVisionUsage


@dataclass
class GPTCompletionsResponse(GPTCompletionsVisionResponse):
    usage: GPTCompletionsUsage


@dataclass
class GPTVisionResponse(GPTCompletionsVisionResponse):
    usage: GPTVisionUsage


@dataclass
class GPTImageDrawResponse(GPTAPIResponse):
    images_prompt: str
    usage: GPTImageDrawUsage
    images_url: list[str] | None = None
    images_bytes: list[bytes] | None = None

    # ToDo: чё это за срань
    def get_images(self) -> list:
        if self.images_bytes:
            return self.images_bytes
        if self.images_url:
            return self.images_url
        return []


@dataclass
class GPTVoiceRecognitionResponse(GPTAPIResponse):
    text: str
    usage: GPTVoiceRecognitionUsage

from abc import ABC
from dataclasses import dataclass

from apps.gpt.usage import (
    GPTImageDrawUsage,
    GPTCompletionsUsage,
    GPTVisionUsage,
    GPTVoiceRecognitionUsage,
    GPTCompletionsVisionUsage,
    GPTUsage
)


class GPTAPIResponse(ABC):
    usage: GPTUsage


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
    usage: GPTImageDrawUsage

    images_prompt: str
    images_bytes: list[bytes] | None = None


@dataclass
class GPTVoiceRecognitionResponse(GPTAPIResponse):
    usage: GPTVoiceRecognitionUsage

    text: str

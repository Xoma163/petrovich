from dataclasses import dataclass

from apps.bot.api.gpt.usage import (
    GPTAPICompletionsUsage,
    GPTAPIImageDrawUsage,
    GPTAPIVoiceRecognitionUsage
)


@dataclass
class GPTAPIResponse:
    pass


@dataclass
class GPTAPICompletionsResponse(GPTAPIResponse):
    text: str
    usage: GPTAPICompletionsUsage | None = None


@dataclass
class GPTAPIImageDrawResponse(GPTAPIResponse):
    images_url: list[str] | None = None
    images_prompt: str | None = None
    images_bytes: list[bytes] | None = None
    usage: GPTAPIImageDrawUsage | None = None


@dataclass
class GPTAPIVoiceRecognitionResponse(GPTAPIResponse):
    text: str
    usage: GPTAPIVoiceRecognitionUsage | None = None

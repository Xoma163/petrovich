from abc import abstractmethod, ABC
from dataclasses import dataclass
from decimal import Decimal

from apps.gpt.models import (
    GPTModel,
    GPTCompletionsVisionModel,
    CompletionModel,
    VisionModel,
    ImageDrawModel,
    VoiceRecognitionModel
)


class GPTUsage(ABC):
    model: GPTModel

    @property
    @abstractmethod
    def total_cost(self) -> float:
        raise NotImplementedError


@dataclass
class GPTCompletionsVisionUsage(GPTUsage):
    model: GPTCompletionsVisionModel
    completion_tokens: int
    prompt_tokens: int

    @property
    def prompt_token_cost(self) -> Decimal:
        return self.model.prompt_1m_token_cost / 1_000_000

    @property
    def completion_token_cost(self) -> Decimal:
        return self.model.completion_1m_token_cost / 1_000_000

    @property
    def total_cost(self) -> Decimal:
        return (self.prompt_tokens * self.prompt_token_cost +
                self.completion_tokens * self.completion_token_cost)


@dataclass
class GPTCompletionsUsage(GPTCompletionsVisionUsage):
    model: CompletionModel


@dataclass
class GPTVisionUsage(GPTCompletionsVisionUsage):
    model: VisionModel


@dataclass
class GPTImageDrawUsage(GPTUsage):
    model: ImageDrawModel
    images_count: int

    @property
    def image_cost(self) -> Decimal:
        return self.model.image_cost

    @property
    def total_cost(self) -> Decimal:
        return self.image_cost * self.images_count


@dataclass
class GPTVoiceRecognitionUsage(GPTUsage):
    model: VoiceRecognitionModel
    voice_duration: float

    @property
    def voice_recognition_cost(self) -> Decimal:
        return self.model.voice_recognition_1_min_cost / 60

    @property
    def total_cost(self) -> Decimal:
        return self.voice_duration * self.voice_recognition_cost

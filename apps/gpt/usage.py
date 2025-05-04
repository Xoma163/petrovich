from abc import abstractmethod, ABC
from dataclasses import dataclass

from apps.gpt.gpt_models.base import GPTCompletionModel, GPTVisionModel, GPTImageDrawModel, GPTVoiceRecognitionModel, \
    GPTCompletionsVisionModel


class GPTUsage(ABC):

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
    def prompt_token_cost(self) -> float:
        return self.model.prompt_token_cost

    @property
    def completion_token_cost(self) -> float:
        return self.model.completion_token_cost

    @property
    def total_cost(self) -> float:
        return self.prompt_tokens * self.prompt_token_cost + self.completion_tokens * self.completion_token_cost


@dataclass
class GPTCompletionsUsage(GPTCompletionsVisionUsage):
    model: GPTCompletionModel


@dataclass
class GPTVisionUsage(GPTCompletionsVisionUsage):
    model: GPTVisionModel


@dataclass
class GPTImageDrawUsage(GPTUsage):
    model: GPTImageDrawModel
    images_count: int

    @property
    def image_cost(self) -> float:
        return self.model.image_cost

    @property
    def total_cost(self) -> float:
        return self.image_cost * self.images_count


@dataclass
class GPTVoiceRecognitionUsage(GPTUsage):
    model: GPTVoiceRecognitionModel
    voice_duration: float

    @property
    def voice_recognition_cost(self) -> float:
        return self.model.voice_recognition_cost

    @property
    def total_cost(self) -> float:
        return self.voice_duration * self.voice_recognition_cost

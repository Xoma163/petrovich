from abc import abstractmethod, ABC
from dataclasses import dataclass
from decimal import Decimal

from apps.commands.gpt.models import (
    GPTModel,
    GPTCompletionsVisionModel,
    CompletionsModel,
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
    input_tokens: int
    output_tokens: int
    input_cached_tokens: int = 0
    web_search_tokens: int = 0

    # --- Цены за 1 токен ---

    @property
    def input_one_token_cost(self) -> Decimal:
        return self.model.input_1m_token_cost / 1_000_000

    @property
    def input_cached_one_token_cost(self) -> Decimal:
        return self.model.input_cached_1m_token_cost / 1_000_000

    @property
    def output_one_token_cost(self) -> Decimal:
        return self.model.output_1m_token_cost / 1_000_000

    @property
    def web_search_one_token_cost(self) -> Decimal:
        return self.model.web_search_1k_token_cost / 1_000

    # --- Цены за потраченное количество токенов ---

    @property
    def input_tokens_cost(self) -> Decimal:
        return self.input_tokens * self.input_one_token_cost

    @property
    def input_cached_tokens_cost(self) -> Decimal:
        return self.input_cached_tokens * self.input_cached_one_token_cost

    @property
    def output_tokens_cost(self) -> Decimal:
        return self.output_tokens * self.output_one_token_cost

    @property
    def web_search_tokens_cost(self) -> Decimal:
        return self.web_search_tokens * self.web_search_one_token_cost

    # --- Итоговая цена ---

    @property
    def total_cost(self) -> Decimal:
        return (
                self.input_tokens_cost +
                self.input_cached_tokens_cost +
                self.output_tokens_cost +
                self.web_search_tokens_cost
        )


@dataclass
class GPTCompletionsUsage(GPTCompletionsVisionUsage):
    model: CompletionsModel


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
    voice_duration: Decimal

    @property
    def voice_recognition_cost(self) -> Decimal:
        return self.model.voice_recognition_1_min_cost / 60

    @property
    def total_cost(self) -> Decimal:
        return self.voice_duration * self.voice_recognition_cost

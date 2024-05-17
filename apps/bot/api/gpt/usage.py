import dataclasses

from apps.bot.api.gpt.models import GPTCompletionModel, GPTImageDrawModel, GPTVoiceModel


@dataclasses.dataclass
class GPTAPIUsage:
    # model: GPTModel

    @property
    def total_cost(self) -> float:
        raise NotImplementedError


@dataclasses.dataclass
class GPTAPICompletionsUsage(GPTAPIUsage):
    model: GPTCompletionModel
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


@dataclasses.dataclass
class GPTAPIImageDrawUsage(GPTAPIUsage):
    model: GPTImageDrawModel
    images_count: int

    @property
    def image_cost(self) -> float:
        return self.model.image_cost

    @property
    def total_cost(self) -> float:
        return self.image_cost * self.images_count


@dataclasses.dataclass
class GPTAPIVoiceRecognitionUsage(GPTAPIUsage):
    model: GPTVoiceModel
    voice_duration: float

    @property
    def voice_recognition_cost(self) -> float:
        return self.model.voice_recognition_cost

    @property
    def total_cost(self) -> float:
        return self.voice_duration * self.voice_recognition_cost

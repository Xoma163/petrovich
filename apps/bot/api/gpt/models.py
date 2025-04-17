from dataclasses import dataclass
from enum import StrEnum


@dataclass
class GPTModel:
    name: str
    verbose_name: str | None

    def __eq__(self, other) -> bool:
        return self.name == other.name


@dataclass
class GPTCompletionModel(GPTModel):
    prompt_1m_token_cost: float | None = None
    completion_1m_token_cost: float | None = None

    @property
    def prompt_token_cost(self):
        return self.prompt_1m_token_cost / 1000000 if self.prompt_1m_token_cost else None

    @property
    def completion_token_cost(self):
        return self.completion_1m_token_cost / 1000000 if self.completion_1m_token_cost else None


@dataclass
class GPTImageDrawModel(GPTModel):
    image_cost: float | None = None
    width: int | None = None
    height: int | None = None


@dataclass
class GPTVoiceRecognitionModel(GPTModel):
    voice_recognition_1_min_cost: float | None = None

    @property
    def voice_recognition_cost(self):
        return self.voice_recognition_1_min_cost / 60 if self.voice_recognition_1_min_cost else None


class GPTModels:
    # o
    O1 = GPTCompletionModel("o1", "o1", 15, 60)
    # O1_PRO = GPTCompletionModel("o1-pro", "o1 pro", 150, 600)
    O1_MINI = GPTCompletionModel("o1-mini", "o1 mini", 1.1, 4.4)
    O3 = GPTCompletionModel("o3", "o3", 10, 40)
    O3_MINI = GPTCompletionModel("o3-mini", "o3 mini", 1.1, 4.4)
    O4_MINI = GPTCompletionModel("o4-mini", "o4 mini", 1.1, 4.4)

    # GPT-4
    GPT_4_1 = GPTCompletionModel("gpt-4.1", "GPT-4.1", 2, 8)
    GPT_4_1_MINI = GPTCompletionModel("gpt-4.1-mini", "GPT-4.1 MINI", 0.4, 1.6)
    GPT_4_1_NANO = GPTCompletionModel("gpt-4.1-nano", "GPT-4.1 NANO", 0.1, 0.4)

    GPT_4_O = GPTCompletionModel("gpt-4o", "GPT-4o", 2.5, 10)
    GPT_4_O_MINI = GPTCompletionModel("gpt-4o-mini", "GPT-4o MINI", 0.15, 0.6)

    GPT_4 = GPTCompletionModel("gpt-4", "GPT-4", 30, 60)
    GPT_4_TURBO = GPTCompletionModel("gpt-4-turbo", "GPT-4 TURBO", 10, 30)
    GPT_4_32K = GPTCompletionModel("gpt-4-32k", "GPT-4 32K", 60, 120)

    GPT_4_5 = GPTCompletionModel("gpt-4.5-preview", "GPT-4.5", 75, 150)

    # GPT-3.5
    GPT_3_5_TURBO_0125 = GPTCompletionModel("gpt-3.5-turbo-0125", "GPT-3.5 TURBO 0125", 0.5, 1.5)
    GPT_3_5_TURBO_1106 = GPTCompletionModel("gpt-3.5-turbo-1106", "GPT-3.5 TURBO 1106", 1, 2)
    GPT_3_5_TURBO_0613 = GPTCompletionModel("gpt-3.5-turbo-0613", "GPT-3.5 TURBO 0613", 1.5, 2)
    GPT_3_5_TURBO_16K_0613 = GPTCompletionModel("gpt-3.5-turbo-16k-0613", "GPT-3.5 TURBO 16K 0613", 3, 4)
    GPT_3_5_TURBO_0301 = GPTCompletionModel("gpt-3.5-turbo-0301", "GPT-3.5 TURBO 16K 0613", 1.5, 2)

    # Image models
    DALLE_3_PORTAIR = GPTImageDrawModel("dall-e-3", "DALLE 3", image_cost=0.08, width=1024, height=1792)
    DALLE_3_PORTAIR_HD = GPTImageDrawModel("dall-e-3", "DALLE 3", image_cost=0.12, width=1792, height=1024)
    DALLE_3_SQUARE = GPTImageDrawModel("dall-e-3", "DALLE 3", image_cost=0.04, width=1024, height=1024)
    DALLE_3_SQUARE_HD = GPTImageDrawModel("dall-e-3", "DALLE 3", image_cost=0.08, width=1024, height=1024)
    DALLE_3_ALBUM = GPTImageDrawModel("dall-e-3", "DALLE 3", image_cost=0.08, width=1792, height=1024)
    DALLE_3_ALBUM_HD = GPTImageDrawModel("dall-e-3", "DALLE 3", image_cost=0.12, width=1792, height=1024)

    # Audio models
    WHISPER = GPTVoiceRecognitionModel("whisper-1", None, voice_recognition_1_min_cost=0.006)

    # older models

    @classmethod
    def get_all_models(cls, _class) -> list:
        return [cls.__dict__[x] for x in cls.__dict__ if isinstance(cls.__dict__[x], _class)]

    @classmethod
    def get_completions_models(cls) -> list[GPTCompletionModel]:
        return cls.get_all_models(GPTCompletionModel)

    @classmethod
    def get_draw_models(cls) -> list[GPTImageDrawModel]:
        return cls.get_all_models(GPTImageDrawModel)

    @classmethod
    def get_model_by_name(cls, name) -> GPTModel:
        models = cls.get_all_models(GPTModel)
        for model in models:
            if model.name == name:
                return model
        raise ValueError


class GPTImageFormat(StrEnum):
    ALBUM = "album"
    PORTAIR = "portair"
    SQUARE = "square"


class GPTImageQuality(StrEnum):
    STANDARD = "standard"
    HIGH = "hd"

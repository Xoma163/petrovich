from dataclasses import dataclass


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


@dataclass
class GPTVoiceRecognitionModel(GPTModel):
    voice_recognition_1_min_cost: float | None = None

    @property
    def voice_recognition_cost(self):
        return self.voice_recognition_1_min_cost / 60 if self.voice_recognition_1_min_cost else None


class GPTModels:
    # GPT-4
    GPT_4_OMNI_MINI = GPTCompletionModel("gpt-4o-mini", "GPT-4 OMNI MINI", 0.15, 0.6)
    GPT_4_OMNI = GPTCompletionModel("gpt-4o", "GPT-4 OMNI", 5, 15)
    GPT_4_TURBO = GPTCompletionModel("gpt-4-turbo", "GPT-4 TURBO", 10, 30)
    GPT_4 = GPTCompletionModel("gpt-4", "GPT-4", 30, 60)
    GPT_4_32K = GPTCompletionModel("gpt-4-32k", "GPT-4 32K", 60, 120)

    # GPT-3.5
    GPT_3_5_TURBO_0125 = GPTCompletionModel("gpt-3.5-turbo-0125", "GPT-3.5 TURBO 0125", 0.5, 1.5)
    GPT_3_5_TURBO_1106 = GPTCompletionModel("gpt-3.5-turbo-1106", "GPT-3.5 TURBO 1106", 1, 2)
    GPT_3_5_TURBO_0613 = GPTCompletionModel("gpt-3.5-turbo-0613", "GPT-3.5 TURBO 0613", 1.5, 2)
    GPT_3_5_TURBO_16K_0613 = GPTCompletionModel("gpt-3.5-turbo-16k-0613", "GPT-3.5 TURBO 16K 0613", 3, 4)
    GPT_3_5_TURBO_0301 = GPTCompletionModel("gpt-3.5-turbo-0301", "GPT-3.5 TURBO 16K 0613", 1.5, 2)

    # image models
    DALLE_3 = GPTImageDrawModel("dall-e-3", "DALLE 3", image_cost=0.12)
    DALLE_2 = GPTImageDrawModel("dall-e-2", "DALLE 2", image_cost=0.02)

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
    def get_image_models(cls) -> list[GPTImageDrawModel]:
        return cls.get_all_models(GPTImageDrawModel)

    @classmethod
    def get_model_by_name(cls, name) -> GPTModel:
        models = cls.get_all_models(GPTModel)
        for model in models:
            if model.name == name:
                return model
        raise ValueError

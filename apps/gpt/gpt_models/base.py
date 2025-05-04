from dataclasses import dataclass


@dataclass
class GPTModel:
    name: str
    verbose_name: str

    def __eq__(self, other) -> bool:
        return self.name == other.name


@dataclass
class GPTCompletionsVisionModel(GPTModel):
    prompt_1m_token_cost: float
    completion_1m_token_cost: float

    @property
    def prompt_token_cost(self):
        return self.prompt_1m_token_cost / 1000000

    @property
    def completion_token_cost(self):
        return self.completion_1m_token_cost / 1000000


@dataclass
class GPTCompletionModel(GPTCompletionsVisionModel):
    pass


@dataclass
class GPTVisionModel(GPTCompletionsVisionModel):
    pass


@dataclass
class GPTImageDrawModel(GPTModel):
    image_cost: float
    width: int
    height: int


@dataclass
class GPTVoiceRecognitionModel(GPTModel):
    voice_recognition_1_min_cost: float

    @property
    def voice_recognition_cost(self):
        return self.voice_recognition_1_min_cost / 60


class GPTModels:
    @classmethod
    def get_all_models(cls, _class) -> list:
        return [
            getattr(cls, name)
            for name in dir(cls)
            if not name.startswith('__') and isinstance(getattr(cls, name), _class)
        ]

    @classmethod
    def get_completions_models(cls) -> list[GPTCompletionModel]:
        return cls.get_all_models(GPTCompletionModel)

    @classmethod
    def get_vision_models(cls) -> list[GPTVisionModel]:
        return cls.get_all_models(GPTVisionModel)

    @classmethod
    def get_draw_models(cls) -> list[GPTImageDrawModel]:
        return cls.get_all_models(GPTImageDrawModel)

    @classmethod
    def get_voice_recognition_models(cls) -> list[GPTVoiceRecognitionModel]:
        return cls.get_all_models(GPTVoiceRecognitionModel)

    @classmethod
    def get_model_by_name(cls, name, _class: type[GPTModel] = GPTModel) -> GPTModel:
        models = cls.get_all_models(_class)
        for model in models:
            if model.name == name:
                return model
        raise ValueError(f'Модель "{name}" не найдена.')

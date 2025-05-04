from apps.gpt.gpt_models.base import GPTModels, GPTCompletionModel, GPTVisionModel, GPTImageDrawModel


class GrokCompletionModels(GPTModels):
    grok_3 = GPTCompletionModel("grok-3", "grok-3", 3, 15)
    grok_3_fast = GPTCompletionModel("grok-3-fast", "grok-3 fast", 5, 25)
    grok_3_mini = GPTCompletionModel("grok-3-mini", "grok-3 mini", 0.3, 0.5)
    grok_3_mini_fast = GPTCompletionModel("grok-3-mini-fast", "grok-3 mini fast", 0.6, 4)
    grok_2 = GPTCompletionModel("grok-2", "grok-2", 2, 10)


class GrokVisionModels(GPTModels):
    grok_2_vision = GPTVisionModel("grok-2-vision", "grok-2 vision", 2, 10)


class GrokImageDrawModels(GPTModels):
    grok_2_image = GPTImageDrawModel("grok-2-image", "grok-2 image", 0.07, 1024, 768)


class GrokModels(GrokCompletionModels, GrokVisionModels, GrokImageDrawModels):
    pass

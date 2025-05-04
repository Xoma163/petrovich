from apps.gpt.gpt_models.base import GPTModels, GPTCompletionModel, GPTVisionModel


class ClaudeCompletionModels(GPTModels):
    claude_3_7_sonnet = GPTCompletionModel("claude-3-7-sonnet-latest", "3.7 Sonnet", 3, 15)
    claude_3_5_sonnet = GPTCompletionModel("claude-3-5-sonnet-latest", "3.5 Sonnet v2", 3, 15)
    claude_3_5_haiku = GPTCompletionModel("claude-3-5-haiku-latest", "3.5 Haiku", 0.8, 4)


class ClaudeVisionModels(GPTModels):
    claude_3_7_sonnet_vision = GPTVisionModel("claude-3-7-sonnet-latest", "3.7 Sonnet", 3, 15)
    claude_3_5_sonnet_vision = GPTVisionModel("claude-3-5-sonnet-latest", "3.5 Sonnet v2", 3, 15)
    claude_3_5_haiku_vision = GPTVisionModel("claude-3-5-haiku-latest", "3.5 Haiku", 0.8, 4)


class ClaudeModels(ClaudeCompletionModels, ClaudeVisionModels):
    pass

from apps.bot.api.gpt.response import GPTAPIResponse


class GPT:
    def __init__(self, **kwargs):
        super().__init__()

    def _get_model(self, use_image=False):
        raise NotImplementedError

    def completions(self, messages: list) -> GPTAPIResponse:
        raise NotImplementedError

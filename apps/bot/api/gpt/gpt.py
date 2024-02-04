from apps.bot.api.gpt.response import GPTAPIResponse


class GPT:
    def __init__(self, model):
        self.model = model
        super().__init__()

    def completions(self, messages: list) -> GPTAPIResponse:
        raise NotImplementedError

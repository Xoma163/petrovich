from apps.bot.api.gpt.message import GPTMessages
from apps.bot.api.gpt.response import GPTAPICompletionsResponse


class GPT:
    def __init__(self, **kwargs):
        super(GPT, self).__init__(**kwargs)

    def _get_model(self, use_image: bool = False):
        raise NotImplementedError

    def completions(self, messages: GPTMessages, use_image: bool = False) -> GPTAPICompletionsResponse:
        raise NotImplementedError

    @property
    def _headers(self) -> dict:
        raise NotImplementedError

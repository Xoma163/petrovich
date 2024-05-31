from apps.bot.api.gpt.message import GPTMessages
from apps.bot.api.gpt.response import GPTAPICompletionsResponse
from apps.bot.api.handler import API


class GPTAPI(API):
    def __init__(self, *args, **kwargs):
        super(GPTAPI, self).__init__(*args, **kwargs)

    def _get_model(self, use_image: bool = False):
        raise NotImplementedError

    def completions(self, messages: GPTMessages, use_image: bool = False) -> GPTAPICompletionsResponse:
        raise NotImplementedError

    @property
    def _headers(self) -> dict:
        raise NotImplementedError

from apps.commands.gpt.api.base import GPTAPI
from apps.commands.gpt.api.providers.qwen import QwenAPI
from apps.commands.gpt.enums import GPTProviderEnum
from apps.commands.gpt.messages.base import GPTMessages
from apps.commands.gpt.messages.openai_completions import OpenAICompletionsMessage
from apps.commands.gpt.providers.base import GPTProvider


class QwenProvider(GPTProvider):
    type_enum: GPTProviderEnum = GPTProviderEnum.QWEN
    messages_class: type[GPTMessages] = OpenAICompletionsMessage
    api_class: type[GPTAPI] = QwenAPI

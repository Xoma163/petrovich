from apps.commands.gpt.api.base import GPTAPI
from apps.commands.gpt.api.providers.hermes import HermesAPI
from apps.commands.gpt.enums import GPTProviderEnum
from apps.commands.gpt.messages.base import GPTMessages
from apps.commands.gpt.messages.openai_completions import OpenAICompletionsMessage
from apps.commands.gpt.providers.base import GPTProvider


class HermesProvider(GPTProvider):
    type_enum: GPTProviderEnum = GPTProviderEnum.HERMES
    messages_class: type[GPTMessages] = OpenAICompletionsMessage
    api_class: type[GPTAPI] = HermesAPI

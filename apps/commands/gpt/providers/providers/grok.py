from apps.commands.gpt.api.base import GPTAPI
from apps.commands.gpt.api.providers.grok import GrokAPI
from apps.commands.gpt.enums import GPTProviderEnum
from apps.commands.gpt.messages.base import GPTMessages
from apps.commands.gpt.messages.providers.grok import GrokMessages
from apps.commands.gpt.providers.base import GPTProvider


class GrokProvider(GPTProvider):
    type_enum: GPTProviderEnum = GPTProviderEnum.GROK
    messages_class: type[GPTMessages] = GrokMessages
    api_class: type[GPTAPI] = GrokAPI

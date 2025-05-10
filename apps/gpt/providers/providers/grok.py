from apps.gpt.api.base import GPTAPI
from apps.gpt.api.providers.grok import GrokAPI
from apps.gpt.enums import GPTProviderEnum
from apps.gpt.messages.base import GPTMessages
from apps.gpt.messages.providers.grok import GrokMessages
from apps.gpt.providers.base import GPTProvider
from petrovich.settings import env


class GrokProvider(GPTProvider):
    type_enum: GPTProviderEnum = GPTProviderEnum.GROK
    messages_class: type[GPTMessages] = GrokMessages
    api_class: type[GPTAPI] = GrokAPI
    api_key: str = env.str("GROK_API_KEY")

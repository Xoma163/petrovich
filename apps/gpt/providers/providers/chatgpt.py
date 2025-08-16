from apps.gpt.api.base import GPTAPI
from apps.gpt.api.providers.chatgpt import ChatGPTAPI
from apps.gpt.enums import GPTProviderEnum
from apps.gpt.messages.base import GPTMessages
from apps.gpt.messages.providers.chatgpt import ChatGPTMessages
from apps.gpt.providers.base import GPTProvider


class ChatGPTProvider(GPTProvider):
    type_enum: GPTProviderEnum = GPTProviderEnum.CHATGPT
    messages_class: type[GPTMessages] = ChatGPTMessages
    api_class: type[GPTAPI] = ChatGPTAPI

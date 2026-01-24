from apps.commands.gpt.api.base import GPTAPI
from apps.commands.gpt.api.providers.chatgpt import ChatGPTAPI
from apps.commands.gpt.enums import GPTProviderEnum
from apps.commands.gpt.messages.base import GPTMessages
from apps.commands.gpt.messages.providers.chatgpt import ChatGPTMessages
from apps.commands.gpt.providers.base import GPTProvider


class ChatGPTProvider(GPTProvider):
    type_enum: GPTProviderEnum = GPTProviderEnum.CHATGPT
    messages_class: type[GPTMessages] = ChatGPTMessages
    api_class: type[GPTAPI] = ChatGPTAPI

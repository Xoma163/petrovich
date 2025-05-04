from dataclasses import dataclass

from apps.gpt.messages.base import GPTMessage
from apps.gpt.messages.openai import OpenAIMessage, OpenAIMessages


@dataclass
class ChatGPTMessage(OpenAIMessage):
    pass


@dataclass
class ChatGPTMessages(OpenAIMessages):
    message_class: type[GPTMessage] = ChatGPTMessage

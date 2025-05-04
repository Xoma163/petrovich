from dataclasses import dataclass

from apps.gpt.messages.base import GPTMessage
from apps.gpt.messages.openai import OpenAIMessage, OpenAIMessages


@dataclass
class GrokMessage(OpenAIMessage):
    pass


@dataclass
class GrokMessages(OpenAIMessages):
    message_class: type[GPTMessage] = GrokMessage

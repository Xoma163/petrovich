import dataclasses
from abc import ABC
from enum import Enum


class GPTMessageRole(Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'


@dataclasses.dataclass
class GPTMessage(ABC):
    role: GPTMessageRole
    text: str
    images: list[str] = None

    def get_message(self) -> dict:
        raise NotImplementedError()


class ChatGPTMessage(GPTMessage):
    def get_message(self) -> dict:
        message = {
            'role': self.role.value,
            'content': [
                {
                    'type': 'text',
                    'text': self.text
                }
            ]
        }
        if self.images:
            for image in self.images:
                message['content'].append({
                    'type': 'image_url',
                    'image_url': {
                        'url': f"data:image/jpeg;base64,{image}"
                    }
                })
        return message


class GigachatGPTMessage(ChatGPTMessage):
    def get_message(self) -> dict:
        return {
            'role': self.role.value,
            'content': self.text
        }


class GeminiGPTMessage(GPTMessage):

    def get_message(self) -> dict:
        message = {
            'role': self._get_role(),
            'parts': [{
                'text': self._get_text()
            }]
        }
        if self.images:
            for image in self.images:
                message['parts'].append({  # noqa
                    'inline_data': {
                        'mime_type': 'image/jpeg',
                        'data': image
                    }
                })
        return message

    def _get_role(self) -> str:
        if self.role == GPTMessageRole.SYSTEM:
            return 'user'
        elif self.role == GPTMessageRole.ASSISTANT:
            return 'model'
        else:
            return GPTMessageRole.USER.value

    def _get_text(self) -> str:
        return f"System prompt: {self.text}" if self.role == GPTMessageRole.SYSTEM else self.text


class GPTMessages(ABC):
    MESSAGE_CLASS = GPTMessage
    MESSAGE_ROLE = GPTMessageRole

    def __init__(self):
        self._messages: list[GPTMessage] = []

    def add_message(self, role, text, images=None):
        message = self.MESSAGE_CLASS(role, text, images)
        self._messages.append(message)

    def get_messages(self) -> list[dict]:
        return [x.get_message() for x in self._messages]

    def reverse(self):
        self._messages.reverse()

    @property
    def last_message(self) -> MESSAGE_CLASS:
        return self._messages[-1]


class ChatGPTMessages(GPTMessages):
    MESSAGE_CLASS = ChatGPTMessage


class GigachatGPTMessages(GPTMessages):
    MESSAGE_CLASS = GigachatGPTMessage

    def add_photo(self, role, text: str, images: list[str]):
        raise NotImplementedError()


class GeminiGPTMessages(GPTMessages):
    MESSAGE_CLASS = GeminiGPTMessage

import dataclasses
from abc import ABC
from enum import StrEnum
from itertools import groupby


class GPTMessageRole(StrEnum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'


@dataclasses.dataclass
class GPTMessage(ABC):
    role: GPTMessageRole
    text: str
    images: list[str] | None = None

    def get_message(self) -> dict:
        raise NotImplementedError


@dataclasses.dataclass
class ChatGPTMessage(GPTMessage):
    def get_message(self) -> dict:
        message = {
            'role': self.role,
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


@dataclasses.dataclass
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
            return GPTMessageRole.USER

    def _get_text(self) -> str:
        return f"System prompt: {self.text}" if self.role == GPTMessageRole.SYSTEM else self.text


@dataclasses.dataclass
class ClaudeGPTMessage(GPTMessage):
    def get_message(self) -> dict:
        message = {
            'role': self.role,
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
                    'type': 'image',
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image
                    },
                })
        return message


class GrokGPTMessage(ChatGPTMessage):
    pass


class GPTMessages(ABC):
    def __init__(self, gpt_message_class: type[GPTMessage]):
        self._messages: list[GPTMessage] = []
        self.message_class: type[GPTMessage] = gpt_message_class

    def add_message(self, role: GPTMessageRole, text: str, images: list[str] | None = None):
        # ToDo: непонятно почему здесь unexpected argument
        message = self.message_class(role, text, images)
        self._messages.append(message)

    def get_messages(self) -> list[dict]:
        return [x.get_message() for x in self._messages]

    def reverse(self):
        self._messages.reverse()

    @property
    def last_message(self) -> GPTMessage:
        return self._messages[-1]


class ChatGPTMessages(GPTMessages):
    def __init__(self):
        super().__init__(ChatGPTMessage)


class GeminiGPTMessages(GPTMessages):
    def __init__(self):
        super().__init__(GeminiGPTMessage)


class ClaudeGPTMessages(GPTMessages):
    def __init__(self):
        super().__init__(ClaudeGPTMessage)

    def get_messages(self) -> list[dict]:
        _messages = [x.get_message() for x in self._messages]
        grouped = groupby(_messages, key=lambda x: x['role'])
        messages = []
        for role, groupped_messages in grouped:
            message = {'role': role, "content": []}
            for groupped_message in groupped_messages:
                for submessage in groupped_message['content']:
                    message['content'].append(submessage)
            messages.append(message)
        return messages


class GrokGPTMessages(GPTMessages):
    def __init__(self):
        super().__init__(GrokGPTMessage)

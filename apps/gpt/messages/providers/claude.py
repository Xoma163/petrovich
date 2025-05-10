from dataclasses import dataclass
from itertools import groupby

from apps.gpt.messages.base import GPTMessage, GPTMessages


@dataclass
class ClaudeMessage(GPTMessage):
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


@dataclass
class ClaudeMessages(GPTMessages):
    message_class: type[GPTMessage] = ClaudeMessage

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

    def __init__(self):
        super().__init__()

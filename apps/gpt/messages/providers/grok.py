from dataclasses import dataclass

from apps.gpt.messages.base import GPTMessage, GPTMessages


@dataclass
class GrokMessage(GPTMessage):
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


@dataclass
class GrokMessages(GPTMessages):
    message_class: type[GPTMessage] = GrokMessage

    def __init__(self):
        super().__init__()

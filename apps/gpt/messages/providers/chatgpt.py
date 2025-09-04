from dataclasses import dataclass

from apps.gpt.messages.base import GPTMessage, GPTMessages
from apps.gpt.messages.consts import GPTMessageRole


@dataclass
class ChatGPTMessage(GPTMessage):
    def get_message(self) -> dict:
        text_type = 'input_text'
        if self.role == GPTMessageRole.ASSISTANT:
            text_type = 'output_text'

        message = {
            'role': self.role,
            'content': [
                {
                    'type': text_type,
                    'text': self.text
                }
            ]
        }
        if self.images:
            for image in self.images:
                message['content'].append({
                    'type': 'input_image',
                    'image_url': f"data:image/jpeg;base64,{image}"
                })
        return message


@dataclass
class ChatGPTMessages(GPTMessages):
    message_class: type[GPTMessage] = ChatGPTMessage

    def __init__(self):
        super().__init__()

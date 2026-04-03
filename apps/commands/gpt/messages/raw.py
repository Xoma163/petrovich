from dataclasses import dataclass

from apps.commands.gpt.messages.consts import GPTMessageRole
from apps.commands.gpt.messages.protocol import GPTMessageProtocol


@dataclass
class RawGPTMessage(GPTMessageProtocol):
    role: GPTMessageRole
    raw: dict

    def get_message(self) -> dict:
        return self.raw

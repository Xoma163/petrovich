from typing import Protocol

from apps.commands.gpt.messages.consts import GPTMessageRole


class GPTMessageProtocol(Protocol):
    role: GPTMessageRole

    def get_message(self) -> dict: ...

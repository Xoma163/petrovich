import dataclasses
from abc import ABC
from abc import abstractmethod

from apps.gpt.messages.consts import GPTMessageRole


@dataclasses.dataclass
class GPTMessage(ABC):
    role: GPTMessageRole
    text: str
    images: list[str] | None = None

    @abstractmethod
    def get_message(self) -> dict:
        raise NotImplementedError


class GPTMessages(ABC):

    @property
    @abstractmethod
    def message_class(self) -> type[GPTMessage]:
        pass

    def __init__(self):
        self.messages: list[GPTMessage] = []

    def add_message(self, role: GPTMessageRole, text: str, images: list[str] | None = None):
        message = self.message_class(role, text, images)  # noqa
        self.messages.append(message)

    def get_messages(self) -> list[dict]:
        return [x.get_message() for x in self.messages]

    def reverse(self):
        self.messages.reverse()

    @property
    def last_message(self) -> GPTMessage:
        return self.messages[-1]

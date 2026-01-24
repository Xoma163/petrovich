import dataclasses
from abc import ABC
from abc import abstractmethod

from apps.bot.core.messages.attachments.document import DocumentAttachment
from apps.bot.core.messages.attachments.photo import PhotoAttachment
from apps.commands.gpt.messages.consts import GPTMessageRole


@dataclasses.dataclass
class GPTMessage(ABC):
    role: GPTMessageRole
    text: str
    images: list[PhotoAttachment] | None = None
    files: list[DocumentAttachment] | None = None

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

    def add_message(
            self,
            role: GPTMessageRole,
            text: str,
            images: list[PhotoAttachment] | None = None,
            files: list[DocumentAttachment] | None = None
    ):
        message = self.message_class(role, text, images, files)  # noqa
        self.messages.append(message)

    def get_messages(self) -> list[dict]:
        return [x.get_message() for x in self.messages]

    def get_preprompt_and_messages(self) -> tuple[str | None, list[dict]]:
        if self.messages[0].role != GPTMessageRole.SYSTEM:
            return None, self.get_messages()
        return self.messages[0].text, [x.get_message() for x in self.messages[1:]]

    def reverse(self):
        self.messages.reverse()

    @property
    def last_message(self) -> GPTMessage:
        return self.messages[-1]

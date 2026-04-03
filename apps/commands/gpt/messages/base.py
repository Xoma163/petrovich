import dataclasses
from abc import ABC
from abc import abstractmethod

from apps.bot.core.messages.attachments.document import DocumentAttachment
from apps.bot.core.messages.attachments.photo import PhotoAttachment
from apps.commands.gpt.messages.consts import GPTMessageRole
from apps.commands.gpt.messages.protocol import GPTMessageProtocol


@dataclasses.dataclass
class GPTMessage(GPTMessageProtocol):
    role: GPTMessageRole
    text: str
    images: list[PhotoAttachment] | None = None
    files: list[DocumentAttachment] | None = None


class GPTMessages(ABC):

    @property
    @abstractmethod
    def message_class(self) -> type[GPTMessage]:
        pass

    def __init__(self):
        self.messages: list[GPTMessageProtocol] = []

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
        result_messages = []
        for message in self.messages:
            result_message = message.get_message()
            if isinstance(result_message, dict):
                result_messages.append(result_message)
            elif isinstance(result_message, list):
                for item in result_message:
                    result_messages.append(item)

        return result_messages

    def get_preprompt_and_messages(self) -> tuple[str | None, list[dict]]:
        if self.messages[0].role != GPTMessageRole.SYSTEM:
            return None, self.get_messages()
        preprompt: str = self.messages[0].text  # noqa
        return preprompt, self.get_messages()[1:]

    def reverse(self):
        self.messages.reverse()

    @property
    def last_message(self) -> GPTMessageProtocol:
        return self.messages[-1]

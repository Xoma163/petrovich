from typing import Protocol

from apps.bot.classes.bots.bot import Bot
from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.attachments.attachment import Attachment
from apps.gpt.providers.base import GPTProvider


class HasCommandFields(Protocol):
    name: str
    bot: Bot
    event: Event
    full_names: list[str]
    provider: GPTProvider
    attachments: list[type[Attachment]]

    def check_attachments(self):
        pass

    def check_conversation(self):
        pass

    def check_pm(self):
        pass

    def check_args(self, x):
        pass

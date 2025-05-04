from typing import Protocol

from apps.bot.classes.bots.bot import Bot
from apps.bot.classes.event.event import Event
from apps.gpt.providers.base import GPTProvider


class HasCommandFields(Protocol):
    name: str
    bot: Bot
    event: Event
    full_names: list[str]
    provider: GPTProvider

    def check_conversation(self):
        pass

    def check_pm(self):
        pass

    def check_args(self, x):
        pass

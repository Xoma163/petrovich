from apps.bot.classes.Command import Command
from apps.bot.utils.utils import random_event


class Clear(Command):
    name = "ясно"
    names = ["ммм"]
    suggest_for_similar = False

    def start(self):
        if self.event.message.command == 'ммм':
            return random_event(["Данон", "Хуета"])
        return "Хуета"

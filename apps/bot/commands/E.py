from apps.bot.classes.Command import Command
from apps.bot.utils.utils import random_event


class E(Command):
    priority = 71

    def accept(self, event):
        return event.message.raw == "ё"

    def start(self):
        return random_event(["ё", "хуё", "моё", "ОТЪЕБИСЬ ОТ Ё", "ты заебал"])

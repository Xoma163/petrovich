from apps.bot.classes.Command import Command
from apps.bot.utils.utils import random_event


class Thanks(Command):
    name = "спасибо"
    names = ["спс", 'ty', 'дякую', 'сяп']

    def start(self):
        return random_event(["Всегда пожалуйста", "На здоровье", "Обращайся", "<3"])

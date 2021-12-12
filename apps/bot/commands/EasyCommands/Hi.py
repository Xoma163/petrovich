from apps.bot.classes.Command import Command
from apps.bot.utils.utils import random_event


class Hi(Command):
    name = "привет"
    names = ["хай", "даров", "дарова", "здравствуй", "здравствуйте", "привки", "прив", "q", "qq", "ку",
             "куку", "здаров", "здарова", "хеей", "хало", "hi", "hello", 'салам']
    mentioned = True

    def start(self):
        return random_event(self.full_names)

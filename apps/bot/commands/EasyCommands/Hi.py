from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import random_event


class Hi(CommonCommand):
    name = "привет"
    names = ["хай", "даров", "дарова", "здравствуй", "здравствуйте", "привки", "прив", "q", "qq", "ку",
             "куку", "здаров", "здарова", "хеей", "хало", "hi", "hello", 'салам']

    def start(self):
        return random_event(self.full_names)

from apps.bot.classes.Command import Command
from apps.bot.utils.utils import random_event


class Rofl(Command):
    name = "орнуть"

    def start(self):
        return random_event(
            ["хд", ":D", "ор", "ору", "😆", ":DDD", "лол", "кек", "лол кек чебурек", "рофл", "ахаха", "АХАХА"])

from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import random_event


class Rofl(CommonCommand):
    names = ["орнуть"]

    def start(self):
        return random_event(
            ["хд", ":D", "ор", "ору", "😆", ":DDD", "лол", "кек", "лол кек чебурек", "рофл", "ахаха", "АХАХА"])

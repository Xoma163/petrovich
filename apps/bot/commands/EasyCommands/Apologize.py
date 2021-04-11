import time

from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import random_event, random_probability


# By E.Korsakov
class Apologize(CommonCommand):
    name = "извинись"
    names = ["извиняйся", "извинитесь"]
    platforms = [Platform.VK, Platform.TG]
    suggest_for_similar = False

    def start(self):
        phrases = ["Извини", "Нет", "Сам извинись", "за что?", "КАВО", "Ты уверен?"]
        phrase = random_event(phrases)
        self.bot.send_message(self.event.peer_id, phrase)
        if phrase == "Извини":
            if random_probability(25):
                time.sleep(3)
                self.bot.send_message(self.event.peer_id, "сь")

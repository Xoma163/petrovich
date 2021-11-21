import time

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.utils.utils import random_event, random_probability


# By E.Korsakov
class Apologize(Command):
    name = "извинись"
    names = ["извиняйся", "извинитесь"]
    platforms = [Platform.VK, Platform.TG]
    suggest_for_similar = False
    non_mentioned = True

    def start(self):
        phrases = ["Извини", "Нет", "Сам извинись", "за что?", "КАВО", "Ты уверен?"]
        phrase = random_event(phrases)
        self.bot.parse_and_send_msgs(phrase, self.event.peer_id)
        if phrase == "Извини":
            if random_probability(25):
                time.sleep(3)
                self.bot.parse_and_send_msgs("сь", self.event.peer_id)

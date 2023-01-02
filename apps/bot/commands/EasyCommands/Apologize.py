import time

from apps.bot.classes.Command import Command
from apps.bot.utils.utils import random_event, random_probability


# By E.Korsakov
class Apologize(Command):
    name = "извинись"
    names = ["извиняйся", "извинитесь"]
    suggest_for_similar = False
    non_mentioned = True

    def start(self):
        phrases = ["Извини", "Нет", "Сам извинись", "за что?", "КАВО", "Ты уверен?", "а может быть ты извинишься?",
                   "ок"]
        phrase = random_event(phrases)
        self.bot.parse_and_send_msgs(phrase, self.event.peer_id, self.event.message_thread_id)
        if phrase == "Извини":
            if random_probability(33):
                time.sleep(3)
                self.bot.parse_and_send_msgs("сь", self.event.peer_id, self.event.message_thread_id)

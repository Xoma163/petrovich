import time

from apps.bot.classes.Command import Command
from apps.bot.classes.messages.ResponseMessage import ResponseMessageItem
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
        rmi = ResponseMessageItem(text=phrase, peer_id=self.event.peer_id,
                                  message_thread_id=self.event.message_thread_id)
        self.bot.send_response_message_item(rmi)
        if phrase == "Извини":
            if random_probability(33):
                time.sleep(3)
                rmi = ResponseMessageItem(text="сь", peer_id=self.event.peer_id,
                                          message_thread_id=self.event.message_thread_id)

                self.bot.send_response_message_item(rmi)

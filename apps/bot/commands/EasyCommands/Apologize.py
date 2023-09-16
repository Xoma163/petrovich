from apps.bot.classes.Command import Command
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import random_event


# By E.Korsakov
class Apologize(Command):
    name = "извинись"
    names = ["извиняйся", "извинитесь"]
    suggest_for_similar = False
    non_mentioned = True

    def start(self) -> ResponseMessage:
        phrases = ["Извини", "Нет", "Сам извинись", "за что?", "КАВО", "Ты уверен?", "а может быть ты извинишься?",
                   "ок"]
        phrase = random_event(phrases)
        return ResponseMessage(ResponseMessageItem(text=phrase))

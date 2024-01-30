from apps.bot.classes.command import Command
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import random_event


# By E.Korsakov
class Apologize(Command):
    name = "извинись"
    names = ["извиняйся", "извинитесь"]
    suggest_for_similar = False
    non_mentioned = True

    def start(self) -> ResponseMessage:
        phrases = ["Извини", "Не", "Сам извинись", "за что?", "КАВО", "Ты уверен?", "а может быть ты извинишься?", "ок"]
        phrase = random_event(phrases)
        return ResponseMessage(ResponseMessageItem(text=phrase))

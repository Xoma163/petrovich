from apps.bot.classes.command import Command
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import random_event


class Thanks(Command):
    name = "спасибо"
    names = ["спс", 'ty', 'дякую', 'сяп']
    mentioned = True

    def start(self) -> ResponseMessage:
        answer = random_event(["Всегда пожалуйста", "На здоровье", "Обращайся", "<3"])
        return ResponseMessage(ResponseMessageItem(text=answer))

from apps.bot.classes.command import Command
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage


class Ping(Command):
    name = "пинг"

    def start(self) -> ResponseMessage:
        answer = "Понг"
        return ResponseMessage(ResponseMessageItem(text=answer))

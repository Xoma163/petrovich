from apps.bot.classes.Command import Command
from apps.bot.classes.messages.ResponseMessage import ResponseMessageItem, ResponseMessage


class Ping(Command):
    name = "пинг"

    def start(self) -> ResponseMessage:
        answer = "Понг"
        return ResponseMessage(ResponseMessageItem(text=answer))

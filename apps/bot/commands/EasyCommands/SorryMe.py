from apps.bot.classes.Command import Command
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem


class SorryMe(Command):
    name = 'извиниться'

    def start(self) -> ResponseMessage:
        answer = f"{self.event.sender} извиняется перед всеми"
        return ResponseMessage(ResponseMessageItem(text=answer))

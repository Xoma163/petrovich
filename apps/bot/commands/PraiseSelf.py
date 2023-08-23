from apps.bot.classes.Command import Command
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem
from apps.bot.commands.Praise import get_praise_or_scold_self


class PraiseSelf(Command):
    name = "похвалиться"
    names = ["похвались", "хвалиться"]

    def start(self) -> ResponseMessage:
        answer = get_praise_or_scold_self(self.event, 'good')
        return ResponseMessage(ResponseMessageItem(text=answer))

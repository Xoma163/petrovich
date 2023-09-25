from apps.bot.classes.command import Command
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.commands.praise import get_praise_or_scold_self


class PraiseSelf(Command):
    name = "похвалиться"
    names = ["похвались", "хвалиться"]

    def start(self) -> ResponseMessage:
        answer = get_praise_or_scold_self(self.event, 'good')
        return ResponseMessage(ResponseMessageItem(text=answer))

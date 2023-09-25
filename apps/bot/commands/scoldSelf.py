from apps.bot.classes.command import Command
from apps.bot.classes.messages.response_message import ResponseMessage
from apps.bot.commands.praise import get_praise_or_scold_self


class ScoldSelf(Command):
    name = "обосраться"
    names = ["обосрись", "поругаться", "поругайся"]

    def start(self) -> ResponseMessage:
        rmi = get_praise_or_scold_self(self.event, 'bad')
        return ResponseMessage(rmi)

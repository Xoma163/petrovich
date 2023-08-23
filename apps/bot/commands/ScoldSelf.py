from apps.bot.classes.Command import Command
from apps.bot.classes.messages.ResponseMessage import ResponseMessage
from apps.bot.commands.Praise import get_praise_or_scold_self


class ScoldSelf(Command):
    name = "обосраться"
    names = ["обосрись", "поругаться", "поругайся"]

    def start(self) -> ResponseMessage:
        rmi = get_praise_or_scold_self(self.event, 'bad')
        return ResponseMessage(rmi)

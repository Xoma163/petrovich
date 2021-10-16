from apps.bot.classes.Command import Command
from apps.bot.commands.Praise import get_praise_or_scold_self


class PraiseSelf(Command):
    name = "похвалиться"
    names = ["похвались", "хвалиться"]

    def start(self):
        return get_praise_or_scold_self(self.event, 'good')

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.commands.Praise import get_praise_or_scold_self


class ScoldSelf(Command):
    name = "обосраться"
    names = ["обосрись", "поругаться", "поругайся"]
    excluded_platforms = [Platform.YANDEX]

    def start(self):
        return get_praise_or_scold_self(self.event, 'bad')

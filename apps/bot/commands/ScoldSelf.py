from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.commands.Praise import get_praise_or_scold_self


class ScoldSelf(CommonCommand):
    names = ["обосраться", "обосрись", "поругаться", "поругайся"]

    def start(self):
        return get_praise_or_scold_self(self.event, 'bad')

from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.commands.Praise import get_praise_or_scold_self


class PraiseSelf(CommonCommand):
    def __init__(self):
        names = ["похвалиться", "похвались", "хвалиться"]
        super().__init__(names)

    def start(self):
        return get_praise_or_scold_self(self.event, 'good')

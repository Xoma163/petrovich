from apps.bot.classes.bots.Bot import Bot as CommonBot
from apps.bot.classes.consts.Consts import Platform


class APIBot(CommonBot):
    def __init__(self):
        CommonBot.__init__(self, Platform.API)

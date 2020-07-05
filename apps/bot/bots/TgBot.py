from threading import Thread

from apps.bot.bots.CommonBot import CommonBot


class TgBot(CommonBot, Thread):
    def __init__(self):
        CommonBot.__init__(self)
        Thread.__init__(self)


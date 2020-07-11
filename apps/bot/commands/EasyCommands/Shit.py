from apps.bot.classes.common.CommonCommand import CommonCommand


class Shit(CommonCommand):
    def __init__(self):
        names = ["дерьмо"]
        super().__init__(names)

    def start(self):
        return "Ня"

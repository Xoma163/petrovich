from apps.bot.classes.common.CommonCommand import CommonCommand


class Shit(CommonCommand):
    def __init__(self):
        names = ["дерьмо"]
        super().__init__(names, suggest_for_similar=False)

    def start(self):
        return "Ня"

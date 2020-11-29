from apps.bot.classes.common.CommonCommand import CommonCommand


class Nya(CommonCommand):
    def __init__(self):
        names = ["ня"]
        super().__init__(names, suggest_for_similar=False)

    def start(self):
        return "Дерьмо"

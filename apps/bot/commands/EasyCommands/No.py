from apps.bot.classes.common.CommonCommand import CommonCommand


class No(CommonCommand):
    def __init__(self):
        names = ["нет"]
        super().__init__(names, suggest_for_similar=False)

    def start(self):
        return "Пидора ответ"

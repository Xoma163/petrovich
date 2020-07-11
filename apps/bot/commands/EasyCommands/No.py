from apps.bot.classes.common.CommonCommand import CommonCommand


class No(CommonCommand):
    def __init__(self):
        names = ["нет"]
        super().__init__(names)

    def start(self):
        return "Пидора ответ"

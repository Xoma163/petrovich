from apps.bot.classes.common.CommonCommand import CommonCommand


class Yes(CommonCommand):
    def __init__(self):
        names = ["да"]
        super().__init__(names)

    def start(self):
        return "Пизда"

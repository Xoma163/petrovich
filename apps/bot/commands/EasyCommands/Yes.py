from apps.bot.classes.common.CommonCommand import CommonCommand


class Yes(CommonCommand):
    def __init__(self):
        names = ["да"]
        super().__init__(names, suggest_for_similar=False)

    def start(self):
        return "Пизда"

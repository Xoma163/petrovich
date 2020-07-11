from apps.bot.classes.common.CommonCommand import CommonCommand


class GayAnswer(CommonCommand):
    def __init__(self):
        names = ["пидора"]
        super().__init__(names)

    def start(self):
        if self.event.args and self.event.args[0].lower() == "ответ":
            return "Шлюхи аргумент"
        return None

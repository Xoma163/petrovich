from apps.bot.classes.common.CommonCommand import CommonCommand


class GayAnswer(CommonCommand):
    def __init__(self):
        names = ["пидора"]
        super().__init__(names)

    def accept(self, event):
        return event.msg == 'пидора ответ'

    def start(self):
        return "Шлюхи аргумент"

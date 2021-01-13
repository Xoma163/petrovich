from apps.bot.classes.common.CommonCommand import CommonCommand


class GayAnswer(CommonCommand):
    def __init__(self):
        names = ["пидора"]
        super().__init__(names, suggest_for_similar=False)

    def accept(self, event):
        return event.clear_msg == 'пидора ответ'

    def start(self):
        return "Шлюхи аргумент"

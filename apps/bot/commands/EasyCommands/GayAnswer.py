from apps.bot.classes.common.CommonCommand import CommonCommand


class GayAnswer(CommonCommand):
    name = "пидора"
    suggest_for_similar = False

    def accept(self, event):
        return event.clear_msg == 'пидора ответ'

    def start(self):
        return "Шлюхи аргумент"

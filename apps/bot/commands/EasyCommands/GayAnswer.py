from apps.bot.classes.Command import Command


class GayAnswer(Command):
    name = "пидора"
    suggest_for_similar = False
    non_mentioned = True

    def accept(self, event):
        return event.message and event.message.clear == 'пидора ответ'

    def start(self):
        return "Шлюхи аргумент"

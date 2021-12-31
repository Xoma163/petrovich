from apps.bot.classes.Command import Command


class WhoreArgument(Command):
    name = "шлюхи"
    suggest_for_similar = False
    non_mentioned = True

    def accept(self, event):
        return event.message and event.message.clear == 'шлюхи аргумент'

    def start(self):
        return "Аргумент не нужен, пидор обнаружен"

from apps.bot.classes.Command import Command


class No(Command):
    name = "нет"
    suggest_for_similar = False

    def start(self):
        return "Пидора ответ"

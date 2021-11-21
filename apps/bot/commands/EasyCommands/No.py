from apps.bot.classes.Command import Command


class No(Command):
    name = "нет"
    suggest_for_similar = False
    non_mentioned = True

    def start(self):
        return "Пидора ответ"

from apps.bot.classes.Command import Command


class Yes(Command):
    name = "Да"
    suggest_for_similar = False

    def start(self):
        return "Пизда"

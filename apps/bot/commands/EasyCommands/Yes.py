from apps.bot.classes.Command import Command


class Yes(Command):
    name = "Да"
    suggest_for_similar = False
    non_mentioned = True

    def start(self):
        return "Пизда"

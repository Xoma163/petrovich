from apps.bot.classes.Command import Command


class Ping(Command):
    name = "пинг"

    def start(self):
        return "Понг"

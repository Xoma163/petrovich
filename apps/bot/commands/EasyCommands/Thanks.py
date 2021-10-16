from apps.bot.classes.Command import Command


class Thanks(Command):
    name = "спасибо"
    names = ["спс", 'ty', 'дякую', 'сяп']

    def start(self):
        return "Всегда пожалуйста :)"

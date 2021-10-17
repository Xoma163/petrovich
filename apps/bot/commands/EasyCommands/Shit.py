from apps.bot.classes.Command import Command


class Shit(Command):
    name = "дерьмо"
    suggest_for_similar = False

    def start(self):
        return "Ня"

from apps.bot.classes.Command import Command


class Shit(Command):
    name = "дерьмо"
    suggest_for_similar = False
    non_mentioned = True

    def start(self):
        return "Ня"

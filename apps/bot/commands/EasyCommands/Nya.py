from apps.bot.classes.Command import Command


class Nya(Command):
    name = "ня"
    suggest_for_similar = False

    def start(self):
        return "Дерьмо"

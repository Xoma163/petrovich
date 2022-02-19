from apps.bot.classes.Command import Command


class Nya(Command):
    name = "ня"
    suggest_for_similar = False
    non_mentioned = True

    def start(self):
        return "Дерьмо"

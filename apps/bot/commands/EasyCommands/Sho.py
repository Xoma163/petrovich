from apps.bot.classes.Command import Command


class Sho(Command):
    name = "шо"
    names = ["шоты", "тышо"]
    suggest_for_similar = False
    non_mentioned = True

    def start(self):
        return "я нишо а ты шо"

from apps.bot.classes.common.CommonCommand import CommonCommand


class Sho(CommonCommand):
    name = "шо"
    names = ["шоты", "тышо"]
    suggest_for_similar = False

    def start(self):
        return "я нишо а ты шо"

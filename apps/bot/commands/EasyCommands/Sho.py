from apps.bot.classes.common.CommonCommand import CommonCommand


class Sho(CommonCommand):
    def __init__(self):
        names = ["шо", "шоты", "тышо"]
        super().__init__(names, suggest_for_similar=False)

    def start(self):
        return "я нишо а ты шо"

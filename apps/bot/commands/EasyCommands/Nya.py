from apps.bot.classes.common.CommonCommand import CommonCommand


class Nya(CommonCommand):
    name = "ня"
    suggest_for_similar = False

    def start(self):
        return "Дерьмо"

from apps.bot.classes.common.CommonCommand import CommonCommand


class Nya(CommonCommand):
    names = ["ня"]
    suggest_for_similar = False

    def start(self):
        return "Дерьмо"

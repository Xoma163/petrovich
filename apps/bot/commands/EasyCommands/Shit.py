from apps.bot.classes.common.CommonCommand import CommonCommand


class Shit(CommonCommand):
    names = ["дерьмо"]
    suggest_for_similar = False

    def start(self):
        return "Ня"

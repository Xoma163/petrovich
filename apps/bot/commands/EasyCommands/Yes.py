from apps.bot.classes.common.CommonCommand import CommonCommand


class Yes(CommonCommand):
    names = ["да"]
    suggest_for_similar = False

    def start(self):
        return "Пизда"

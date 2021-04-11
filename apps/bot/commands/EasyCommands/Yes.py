from apps.bot.classes.common.CommonCommand import CommonCommand


class Yes(CommonCommand):
    name = "Да"
    suggest_for_similar = False

    def start(self):
        return "Пизда"

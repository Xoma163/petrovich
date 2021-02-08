from apps.bot.classes.common.CommonCommand import CommonCommand


class Ping(CommonCommand):
    names = ["пинг"]

    def start(self):
        return "Понг"

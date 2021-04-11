from apps.bot.classes.common.CommonCommand import CommonCommand


class Ping(CommonCommand):
    name = "пинг"

    def start(self):
        return "Понг"

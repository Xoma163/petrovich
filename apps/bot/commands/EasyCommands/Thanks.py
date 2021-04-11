from apps.bot.classes.common.CommonCommand import CommonCommand


class Thanks(CommonCommand):
    name = "спасибо"
    names = ["спс", 'ty', 'дякую', 'сяп']

    def start(self):
        return "Всегда пожалуйста :)"

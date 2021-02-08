from apps.bot.classes.common.CommonCommand import CommonCommand


class Thanks(CommonCommand):
    names = ["спасибо", "спасибо!", "спс", 'ty', 'дякую', 'сяп']

    def start(self):
        return "Всегда пожалуйста :)"

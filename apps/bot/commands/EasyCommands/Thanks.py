from apps.bot.classes.common.CommonCommand import CommonCommand


class Thanks(CommonCommand):
    def __init__(self):
        names = ["спасибо", "спасибо!", "спс", 'ty', 'дякую']
        super().__init__(names)

    def start(self):
        return "Всегда пожалуйста :)"

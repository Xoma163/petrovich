from apps.bot.classes.common.CommonCommand import CommonCommand


class SorryMe(CommonCommand):
    def __init__(self):
        names = ['извиниться']
        super().__init__(names)

    def start(self):
        return f"{self.event.sender} извиняется перед всеми"

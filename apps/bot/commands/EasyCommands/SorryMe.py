from apps.bot.classes.common.CommonCommand import CommonCommand


class SorryMe(CommonCommand):
    name = 'извиниться'

    def start(self):
        return f"{self.event.sender} извиняется перед всеми"

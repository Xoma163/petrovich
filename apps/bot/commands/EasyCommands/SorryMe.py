from apps.bot.classes.Command import Command


class SorryMe(Command):
    name = 'извиниться'

    def start(self):
        return f"{self.event.sender} извиняется перед всеми"

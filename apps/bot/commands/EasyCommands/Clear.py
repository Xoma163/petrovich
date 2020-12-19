from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import random_event


class Clear(CommonCommand):
    def __init__(self):
        names = ["ясно", "ммм"]
        super().__init__(names, suggest_for_similar=False)

    def start(self):
        if self.event.command == 'ммм':
            return random_event(["Данон", "Хуета"])
        return "Хуета"

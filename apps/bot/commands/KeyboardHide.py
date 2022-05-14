from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform


class KeyboardHide(Command):
    name = "скрыть"
    help_text = "убирает клавиатуру"

    platforms = [Platform.VK]

    EMPTY_KEYBOARD = {
        "one_time": False,
        "buttons": []
    }

    def start(self):
        return {'keyboard': self.EMPTY_KEYBOARD}

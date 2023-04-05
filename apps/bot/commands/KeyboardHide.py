from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform


class KeyboardHide(Command):
    name = "скрыть"
    help_text = "убирает клавиатуру"

    platforms = [Platform.VK, Platform.TG]

    EMPTY_KEYBOARD_VK = {
        "one_time": False,
        "buttons": []
    }
    EMPTY_KEYBOARD_TG = {
        'inline_keyboard': {
            'remove_keyboard': True
        }
    }

    def start(self):
        if self.event.platform == Platform.VK:
            return {'keyboard': self.EMPTY_KEYBOARD_VK}
        elif self.event.platform == Platform.TG:
            return {'keyboard': self.EMPTY_KEYBOARD_TG}

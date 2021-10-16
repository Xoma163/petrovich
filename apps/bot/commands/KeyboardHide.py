from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform


class KeyboardHide(Command):
    name = "скрыть"
    help_text = "Скрыть - убирает клавиатуру"

    platforms = [Platform.VK]

    def start(self):
        from apps.bot.initial import EMPTY_KEYBOARD
        return {'keyboard': EMPTY_KEYBOARD}

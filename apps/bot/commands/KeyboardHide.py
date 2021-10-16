from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.Command import Command


# ToDo: TG клавы
class KeyboardHide(Command):
    name = "скрыть"
    help_text = "Скрыть - убирает клавиатуру"

    platforms = [Platform.VK, Platform.TG]

    def start(self):
        from apps.bot.initial import EMPTY_KEYBOARD
        return {'keyboard': EMPTY_KEYBOARD}

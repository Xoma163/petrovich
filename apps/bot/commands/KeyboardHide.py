from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand


# ToDo: TG клавы
class KeyboardHide(CommonCommand):
    name = "скрыть"
    help_text = "Скрыть - убирает клавиатуру"

    platforms = [Platform.VK, Platform.TG]

    def start(self):
        from apps.bot.initial import EMPTY_KEYBOARD
        return {'keyboard': EMPTY_KEYBOARD}

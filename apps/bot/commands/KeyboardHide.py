from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand


# ToDo: TG клавы
class KeyboardHide(CommonCommand):
    names = ["скрыть", "убери"]
    help_text = "Скрыть - убирает клавиатуру"
    keyboard = {'text': 'Скрыть', 'color': 'gray', 'row': 3, 'col': 1}

    platforms = [Platform.VK, Platform.TG]

    def start(self):
        from apps.bot.initial import EMPTY_KEYBOARD
        return {'keyboard': EMPTY_KEYBOARD}

from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand


# ToDo: TG клавы
class KeyboardHide(CommonCommand):

    def __init__(self):
        names = ["скрыть", "убери"]
        help_text = "Скрыть - убирает клавиатуру"
        keyboard = {'text': 'Скрыть', 'color': 'gray', 'row': 3, 'col': 1}

        super().__init__(names, help_text, keyboard=keyboard, platforms=[Platform.VK, Platform.TG], enabled=False)

    def start(self):
        from apps.bot.initial import EMPTY_KEYBOARD
        return {'keyboard': EMPTY_KEYBOARD}

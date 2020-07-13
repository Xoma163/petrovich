from apps.bot.classes.common.CommonCommand import CommonCommand


# ToDo: TG
class KeyboardHide(CommonCommand):

    def __init__(self):
        names = ["скрыть", "убери"]
        help_text = "Скрыть - убирает клавиатуру"
        keyboard = {'text': 'Скрыть', 'color': 'gray', 'row': 3, 'col': 1}

        super().__init__(names, help_text, keyboard=keyboard, platforms=['vk','tg'], enabled=False)

    def start(self):
        from apps.bot.initial import EMPTY_KEYBOARD
        return {'keyboard': EMPTY_KEYBOARD}

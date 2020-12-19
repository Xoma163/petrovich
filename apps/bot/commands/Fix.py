from apps.bot.classes.Consts import Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import has_cyrillic

_eng_chars = u"~`!@#$%^&qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"
_rus_chars = u"ёё!\"№;%:?йцукенгшщзхъфывапролджэячсмитьбю.ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,"
_trans_table = dict(zip(_eng_chars, _rus_chars))
_trans_table_reverse = dict(zip(_rus_chars, _eng_chars))


def fix_layout(s, reverse):
    if not reverse:
        return u''.join([_trans_table.get(c, c) for c in s])
    else:
        return u''.join([_trans_table_reverse.get(c, c) for c in s])


class Fix(CommonCommand):
    def __init__(self):
        names = ["фикс", "раскладка"]
        help_text = "Фикс - исправляет раскладку текста"
        detail_help_text = "Фикс (Пересылаемые сообщения) - исправляет раскладку текста\n" \
                           "Фикс (текст) - исправляет раскладку текста"
        super().__init__(names, help_text, detail_help_text, platforms=[Platform.VK, Platform.TG])

    def start(self):
        if self.event.args:
            msgs = fix_layout(self.event.original_args, has_cyrillic(self.event.original_args))
        elif self.event.fwd:
            msgs = ""
            for msg in self.event.fwd:
                if msg['text']:
                    msgs += f"{fix_layout(msg['text'], has_cyrillic(msg['text']))}\n"
            if not msgs:
                raise PWarning("Нет текста в сообщении или пересланных сообщениях")
        else:
            raise PWarning("Перешлите сообщение или укажите текст в аргументах команды")
        return msgs

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning

_eng_chars = u"~`!@#$%^&qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"
_rus_chars = u"ёё!\"№;%:?йцукенгшщзхъфывапролджэячсмитьбю.ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,"
_trans_table = dict(zip(_eng_chars, _rus_chars))
_trans_table_reverse = dict(zip(_rus_chars, _eng_chars))


def fix_layout(s):
    new_s = ""
    for letter in s:
        if letter in _trans_table:
            new_s += _trans_table[letter]
        elif letter in _trans_table_reverse:
            new_s += _trans_table_reverse[letter]
        else:
            new_s += letter
    return new_s


class Fix(Command):
    name = "фикс"
    names = ["раскладка"]
    help_text = "исправляет раскладку текста"
    help_texts = [
        "(Пересылаемые сообщения) - исправляет раскладку текста",
        "(текст) - исправляет раскладку текста"
    ]
    platforms = [Platform.VK, Platform.TG]
    args_or_fwd = 1

    def start(self):
        if self.event.message.args:
            msgs = fix_layout(self.event.message.args_str)
        else:
            msgs = ""
            for fwd in self.event.fwd:
                if fwd.message and fwd.message.raw:
                    msgs += f"{fix_layout(fwd.message.raw)}"
            if not msgs:
                raise PWarning("Нет текста в сообщении или пересланных сообщениях")
        return msgs

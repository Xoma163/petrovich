from apps.bot.classes.Consts import Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand


class Uyu(CommonCommand):
    name = "уъу"
    names = ["ъуъ"]
    help_text = "Добавляет слово в текст (уъуфикация)"
    help_texts = ["(Пересланные сообщения) [новое слово=бля] - добавляет слово в текст (уъуфикация)"]
    excluded_platforms = [Platform.YANDEX]

    def start(self):
        add_word = "бля"
        if self.event.message.args_str:
            add_word = self.event.message.args_str

        msgs = self.event.fwd
        if msgs is None:
            return add_word
        new_msg = ""
        for msg in msgs:
            if msg['text']:
                new_msg += msg['text'] + "\n"

        new_msg = new_msg.strip()
        if not new_msg:
            raise PWarning("Нет текста в сообщении или пересланных сообщениях")

        symbols_first_priority = ['...']
        symbols_left = ['.', ',', '?', '!', ':']
        symbols_right = [' —', ' -']
        flag = False
        if new_msg[-1] not in symbols_left:
            new_msg += '.'
            flag = True
        for symbol in symbols_first_priority:
            new_msg = new_msg.replace(symbol, " " + add_word + symbol)
        for symbol in symbols_left:
            new_msg = new_msg.replace(symbol, " " + add_word + symbol)
        for symbol in symbols_right:
            new_msg = new_msg.replace(symbol, " " + add_word + " " + symbol)
        if flag:
            new_msg = new_msg[:-1]
        return new_msg

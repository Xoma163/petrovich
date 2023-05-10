from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Exceptions import PWarning


class Uyu(Command):
    name = "уъу"
    names = ["ъуъ"]
    help_text = "добавляет слово в текст (уъуфикация)"
    help_texts = ["(Пересланные сообщения) [новое слово=бля] - добавляет слово в текст (уъуфикация)"]

    def start(self):
        if self.event.chat and not self.event.chat.use_swear:
            add_word = "ня"
        else:
            add_word = "бля"
        if self.event.message.args_str:
            add_word = self.event.message.args_str

        msgs = [x.message.raw for x in self.event.fwd if x.message]
        if not msgs:
            return add_word
        new_msg = "\n\n".join(msgs).strip()

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

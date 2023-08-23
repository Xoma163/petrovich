from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import fix_layout


class Fix(Command):
    name = "фикс"
    names = ["раскладка"]
    help_text = "исправляет раскладку текста"
    help_texts = [
        "(Пересылаемые сообщения) - исправляет раскладку текста",
        "(текст) - исправляет раскладку текста"
    ]
    args_or_fwd = 1

    def start(self) -> ResponseMessage:
        if self.event.message.args:
            msgs = fix_layout(self.event.message.args_str)
        else:
            msgs = ""
            for fwd in self.event.fwd:
                if fwd.message and fwd.message.raw:
                    msgs += f"{fix_layout(fwd.message.raw)}"
            if not msgs:
                raise PWarning("Нет текста в сообщении или пересланных сообщениях")
        answer = msgs
        return ResponseMessage(ResponseMessageItem(text=answer))

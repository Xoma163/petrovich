from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextItem, HelpText, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import fix_layout


class Fix(Command):
    name = "фикс"
    names = ["раскладка"]

    help_text = HelpText(
        commands_text="исправляет раскладку текста",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand("(текст)", "присылает исправленный текст"),
                HelpTextItemCommand("(Пересылаемые сообщения)", "присылает исправленный текст")
            ])
        ]
    )

    args_or_fwd = True

    def start(self) -> ResponseMessage:
        if self.event.message.args:
            msgs = fix_layout(self.event.message.args_str)
        elif self.event.message.quote:
            msgs = self.event.message.quote
        else:
            msgs = ""
            for fwd in self.event.fwd:
                if fwd.message and fwd.message.raw:
                    msgs += f"{fix_layout(fwd.message.raw)}"
            if not msgs:
                raise PWarning("Нет текста в сообщении или пересланных сообщениях")
        answer = msgs
        return ResponseMessage(ResponseMessageItem(text=answer))

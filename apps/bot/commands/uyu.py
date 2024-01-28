from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextItem, HelpText, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Uyu(Command):
    name = "ъуъ"
    names = ["уъу"]

    help_text = HelpText(
        commands_text="добавляет слово в текст (уъуфикация)",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand(
                    "(Пересланные сообщения) [новое слово=бля]", "добавляет слово в текст (уъуфикация)")
            ])
        ]
    )

    def start(self) -> ResponseMessage:
        if self.event.sender.settings.use_swear:
            add_word = "бля"
        else:
            add_word = "ня"

        if self.event.message.args_str:
            add_word = self.event.message.args_str

        msgs = [x.message.raw for x in self.event.fwd if x.message]
        if not msgs:
            return ResponseMessage(ResponseMessageItem(add_word))
        answer = "\n\n".join(msgs).strip()

        if not answer:
            raise PWarning("Нет текста в сообщении или пересланных сообщениях")

        symbols_first_priority = ['...']
        symbols_left = ['.', ',', '?', '!', ':']
        symbols_right = [' —', ' -']
        flag = False
        if answer[-1] not in symbols_left:
            answer += '.'
            flag = True
        for symbol in symbols_first_priority:
            answer = answer.replace(symbol, " " + add_word + symbol)
        for symbol in symbols_left:
            answer = answer.replace(symbol, " " + add_word + symbol)
        for symbol in symbols_right:
            answer = answer.replace(symbol, " " + add_word + " " + symbol)
        if flag:
            answer = answer[:-1]
        return ResponseMessage(ResponseMessageItem(text=answer))

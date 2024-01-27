from apps.bot.api.fucking_great_advice import FuckingGreatAdvice
from apps.bot.classes.command import Command
from apps.bot.classes.const.exceptions import PError
from apps.bot.classes.help_text import HelpText
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Advice(Command):
    name = "совет"

    help_text = HelpText(
        commands_text="даёт случайный совет",
    )

    def start(self) -> ResponseMessage:
        try:
            fga = FuckingGreatAdvice()
            answer = fga.get_advice()
            button = self.bot.get_button("Ещё", self.name)
            keyboard = self.bot.get_inline_keyboard([button])
            return ResponseMessage(ResponseMessageItem(text=answer, keyboard=keyboard))
        except Exception:
            raise PError("Ошибка API")

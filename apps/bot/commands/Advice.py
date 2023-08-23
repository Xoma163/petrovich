from apps.bot.APIs.FuckingGreatAdviceAPI import FuckingGreatAdviceAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Exceptions import PError
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem


class Advice(Command):
    name = "совет"
    name_tg = "advice"

    help_text = "даёт случайный совет"

    def start(self) -> ResponseMessage:
        try:
            fga = FuckingGreatAdviceAPI()
            answer = fga.get_advice()
            button = self.bot.get_button("Ещё", self.name)
            keyboard = self.bot.get_inline_keyboard([button])
            return ResponseMessage(ResponseMessageItem(text=answer, keyboard=keyboard))
        except Exception:
            raise PError("Ошибка API")

from apps.bot.APIs.FuckingGreatAdviceAPI import FuckingGreatAdviceAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Exceptions import PError


class Advice(Command):
    name = "совет"
    name_tg = "advice"

    help_text = "даёт случайный совет"

    def start(self):
        try:
            fga = FuckingGreatAdviceAPI()
            advice = fga.get_advice()
            button = self.bot.get_button("Ещё", self.name)
            keyboard = self.bot.get_inline_keyboard([button])
            return {"text": advice, "keyboard": keyboard}

        except Exception:
            raise PError("Ошибка API")

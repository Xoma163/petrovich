from apps.bot.APIs.FuckingGreatAdviceAPI import FuckingGreatAdviceAPI
from apps.bot.classes.consts.Exceptions import PError
from apps.bot.classes.Command import Command


class Advice(Command):
    name = "совет"
    help_text = "даёт случайный совет"

    def start(self):
        try:
            fga = FuckingGreatAdviceAPI()
            advice = fga.get_advice()
            keyboard = self.bot.get_inline_keyboard([{'command': self.name, 'button_text': "Ещё"}])
            return {"msg": advice, "keyboard": keyboard}

        except:
            raise PError("Ошибка API")

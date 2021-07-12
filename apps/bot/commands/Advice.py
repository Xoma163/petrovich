from apps.bot.APIs.FuckingGreatAdviceAPI import FuckingGreatAdviceAPI
from apps.bot.classes.Exceptions import PError
from apps.bot.classes.common.CommonCommand import CommonCommand


class Advice(CommonCommand):
    name = "совет"
    help_text = "даёт случайный совет"

    def start(self):
        try:
            fga = FuckingGreatAdviceAPI()
            advice = fga.get_advice()
            keyboard = self.bot.get_inline_keyboard(self.name, "Ещё")
            return {"msg": advice, "keyboard": keyboard}

        except:
            raise PError("Ошибка API")

from apps.bot.APIs.RzhunemoguAPI import RzhunemoguAPI
from apps.bot.classes.Command import Command


class Joke(Command):
    name = "анекдот"
    names = ["анек"]
    name_tg = "joke"

    help_text = "присылает случайный анекдот"
    help_texts = [
        "[N=1] - присылает случайный анекдот. N=;\n"
        "1 — Анекдоты\n"
        "2 — Рассказы\n"
        "3 — Стишки\n"
        "4 — Афоризмы\n"
        "5 — Цитаты\n"
        "6 — Тосты\n"
        "8 — Статусы\n"
        "11 — Анекдоты (18+)\n"
        "12 — Рассказы (18+)\n"
        "13 — Стишки (18+)\n"
        "14 — Афоризмы (18+)\n"
        "15 — Цитаты (18+)\n"
        "16 — Тосты (18+)\n"
        "18 — Статусы (18+)\n"
    ]
    int_args = [0]

    def start(self):
        if not self.event.message.args:
            a_type = 1
        else:
            a_type = self.event.message.args[0]
            self.check_number_arg_range(a_type, 1, 19, [9, 10, 17, 19])
        rzhunemogu_api = RzhunemoguAPI()
        msg = rzhunemogu_api.get_joke(a_type)
        return {"text": msg, "keyboard": self.bot.get_inline_keyboard(
            [{'command': self.name, 'button_text': "Ещё", 'args': [a_type]}])}

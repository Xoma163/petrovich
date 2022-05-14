from apps.bot.APIs.BashAPI import BashAPI
from apps.bot.classes.Command import Command

MAX_QUOTES = 20


class Bash(Command):
    name = "баш"
    name_tg = "bash"

    help_text = "рандомная цитата с баша"
    help_texts = ["[количество=5] - рандомная цитата с баша. Максимум 20 цитат"]

    int_args = [0]

    def start(self):
        quotes_count = 5
        if self.event.message.args:
            self.parse_int()
            quotes_count = self.event.message.args[0]
            self.check_number_arg_range(quotes_count, 1, MAX_QUOTES)
        bash_api = BashAPI(quotes_count)
        msg = bash_api.parse()
        button = self.bot.get_button("Ещё", self.name, [quotes_count])
        return {"text": msg, "keyboard": self.bot.get_inline_keyboard([button])}

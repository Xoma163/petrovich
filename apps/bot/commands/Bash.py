from apps.bot.APIs.BashAPI import BashAPI
from apps.bot.classes.common.CommonCommand import CommonCommand

MAX_QUOTES = 20


class Bash(CommonCommand):
    name = "баш"
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
        return {
            "msg": msg,


            "keyboard": self.bot.get_inline_keyboard([{'command': self.name, 'button_text': "Ещё", 'args':{"quotes_count": quotes_count}}])
        }

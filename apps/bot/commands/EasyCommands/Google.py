from urllib.parse import quote

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform


class Google(Command):
    name = "гугл"
    help_text = "формирует ссылку в гугл"
    help_texts = ["(текст) - формирует ссылку в гугл"]
    args = 1

    def start(self):
        if self.event.platform == Platform.TG:
            url = f"https://www.google.com/search?q={quote(self.event.message.args_str_case)}"
            return {'text': f"[Окей Гугл, {self.event.message.args_str_case}]({url})",'parse_mode':'markdown'}
        return


from urllib.parse import quote

from apps.bot.classes.Command import Command


class Google(Command):
    name = "гугл"
    help_text = "формирует ссылку в гугл"
    help_texts = ["(текст) - формирует ссылку в гугл"]
    args = 1

    def start(self):
        return f"https://www.google.com/search?q={quote(self.event.message.args_str)}"

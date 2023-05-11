from urllib.parse import quote

from apps.bot.classes.Command import Command


class Google(Command):
    name = "гугл"
    names = ["google", "ggl", "гугле", "гоогле"]
    help_text = "формирует ссылку в гугл"
    help_texts = ["(текст) - формирует ссылку в гугл"]
    args = 1

    def start(self):
        url = f"https://www.google.com/search?q={quote(self.event.message.args_str_case)}"
        return self.bot.get_formatted_url(f"Окей Гугл {self.event.message.args_str_case}", url)

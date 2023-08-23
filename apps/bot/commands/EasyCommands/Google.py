from urllib.parse import quote

from apps.bot.classes.Command import Command
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem


class Google(Command):
    name = "гугл"
    names = ["google", "ggl", "гугле", "гоогле"]
    help_text = "формирует ссылку в гугл"
    help_texts = ["(текст) - формирует ссылку в гугл"]
    args = 1

    def start(self) -> ResponseMessage:
        url = f"https://www.google.com/search?q={quote(self.event.message.args_str_case)}"
        answer = self.bot.get_formatted_url(f"Окей Гугл {self.event.message.args_str_case}", url)
        return ResponseMessage(ResponseMessageItem(text=answer))

from apps.bot.classes.command import Command
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Git(Command):
    name = "гит"
    names = ["гитхаб"]
    name_tg = 'github'

    help_text = "ссылка на гитхаб"

    def start(self) -> ResponseMessage:
        url = 'https://github.com/Xoma163/petrovich/'
        answer = self.bot.get_formatted_url("Гитхаб", url)
        return ResponseMessage(ResponseMessageItem(text=answer))

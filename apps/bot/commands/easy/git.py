from apps.bot.classes.command import Command
from apps.bot.classes.help_text import HelpText
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Git(Command):
    name = "гит"
    names = ["гитхаб"]

    help_text = HelpText(
        commands_text="ссылка на гитхаб",
    )

    URL = 'https://github.com/Xoma163/petrovich/'

    def start(self) -> ResponseMessage:
        answer = self.bot.get_formatted_url("Гитхаб", self.URL)
        return ResponseMessage(ResponseMessageItem(text=answer))

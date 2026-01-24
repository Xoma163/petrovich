from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.commands.command import Command
from apps.commands.help_text import HelpText


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

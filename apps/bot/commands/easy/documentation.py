from apps.bot.classes.command import Command
from apps.bot.classes.help_text import HelpText
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Documentation(Command):
    name = "документация"
    names = ["дока"]

    help_text = HelpText(
        commands_text="ссылка на документацию",
    )

    URL = 'https://github.com/Xoma163/petrovich/wiki/1.1-Документация-для-пользователей'

    def start(self) -> ResponseMessage:
        answer = self.bot.get_formatted_url("Документация", self.URL)
        return ResponseMessage(ResponseMessageItem(text=answer))

from apps.bot.classes.command import Command
from apps.bot.classes.help_text import HelpText
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Documentation(Command):
    name = "документация"
    names = ["дока"]

    help_text = HelpText(
        commands_text="ссылка на документацию",
    )

    def start(self) -> ResponseMessage:
        url = 'https://github.com/Xoma163/petrovich/wiki/1.1-Документация-для-пользователей'
        answer = self.bot.get_formatted_url("Документация", url)

        return ResponseMessage(ResponseMessageItem(text=answer))

from apps.bot.classes.command import Command
from apps.bot.classes.help_text import HelpText
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Issues(Command):
    name = "баги"
    names = ["ишюс", "ишьюс", "иши"]

    help_text = HelpText(
        commands_text="список проблем",
    )

    URL = "https://github.com/Xoma163/petrovich/issues"

    def start(self) -> ResponseMessage:
        answer = self.bot.get_formatted_url("Ишюсы", self.URL)
        return ResponseMessage(ResponseMessageItem(text=answer))

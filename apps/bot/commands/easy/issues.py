from apps.bot.classes.command import Command
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Issues(Command):
    name = "баги"
    name_tg = 'issues'
    names = ["ишюс", "ишьюс", "иши"]

    help_text = "список проблем"

    def start(self) -> ResponseMessage:
        url = "https://github.com/Xoma163/petrovich/issues"
        answer = self.bot.get_formatted_url("Ишюс", url)
        return ResponseMessage(ResponseMessageItem(text=answer))
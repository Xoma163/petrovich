from apps.bot.classes.Command import Command
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem


class Issues(Command):
    name = "баги"
    name_tg = 'issues'
    names = ["ишюс", "ишьюс", "иши"]

    help_text = "список проблем"

    def start(self):
        url = "https://github.com/Xoma163/petrovich/issues"
        answer = self.bot.get_formatted_url("Ишюс", url)

        return ResponseMessage(
            ResponseMessageItem(
                text=answer,
                peer_id=self.event.peer_id,
                message_thread_id=self.event.message_thread_id
            )
        )

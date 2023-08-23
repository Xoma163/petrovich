from apps.bot.classes.Command import Command
from apps.bot.classes.messages.ResponseMessage import ResponseMessageItem, ResponseMessage


class Ping(Command):
    name = "пинг"

    def start(self):
        answer = "Понг"

        return ResponseMessage(
            ResponseMessageItem(
                text=answer,
                peer_id=self.event.peer_id,
                message_thread_id=self.event.message_thread_id
            )
        )

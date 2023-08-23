from apps.bot.classes.Command import Command
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem


class WhoreArgument(Command):
    name = "шлюхи"
    suggest_for_similar = False
    non_mentioned = True

    def accept(self, event):
        return event.message and event.message.clear == 'шлюхи аргумент'

    def start(self):
        answer = "Аргумент не нужен, пидор обнаружен"

        return ResponseMessage(
            ResponseMessageItem(
                text=answer,
                peer_id=self.event.peer_id,
                message_thread_id=self.event.message_thread_id
            )
        )

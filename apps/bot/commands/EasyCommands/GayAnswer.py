from apps.bot.classes.Command import Command
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem


class GayAnswer(Command):
    name = "пидора"
    suggest_for_similar = False
    non_mentioned = True

    def accept(self, event):
        if event.chat and not event.chat.use_swear:
            return False
        return event.message and event.message.clear == 'пидора ответ'

    def start(self):
        answer = "Шлюхи аргумент"

        return ResponseMessage(
            ResponseMessageItem(
                text=answer,
                peer_id=self.event.peer_id,
                message_thread_id=self.event.message_thread_id
            )
        )

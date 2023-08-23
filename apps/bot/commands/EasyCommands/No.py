from apps.bot.classes.Command import Command
from apps.bot.classes.events.Event import Event
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem


class No(Command):
    name = "нет"
    args = 0
    suggest_for_similar = False
    non_mentioned = True

    def accept(self, event: Event):
        if event.chat and not event.chat.use_swear:
            return False
        if event.message and len(event.message.args) == 0:
            return super().accept(event)

    def start(self):
        answer = "Пидора ответ"

        return ResponseMessage(
            ResponseMessageItem(
                text=answer,
                peer_id=self.event.peer_id,
                message_thread_id=self.event.message_thread_id
            )
        )

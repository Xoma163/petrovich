from apps.bot.classes.command import Command
from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage


class Yes(Command):
    name = "Да"
    args = 0
    suggest_for_similar = False
    non_mentioned = True

    def accept(self, event: Event) -> bool:
        if event.chat and not event.chat.use_swear:
            return False
        if event.message and len(event.message.args) == 0:
            return super().accept(event)

    def start(self) -> ResponseMessage:
        answer = "Пизда"
        return ResponseMessage(ResponseMessageItem(text=answer))
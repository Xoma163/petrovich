from apps.bot.classes.command import Command
from apps.bot.classes.event import Event
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class GayAnswer(Command):
    name = "пидора"
    suggest_for_similar = False
    non_mentioned = True

    def accept(self, event: Event) -> bool:
        if event.chat and not event.chat.use_swear:
            return False
        return event.message and event.message.clear == 'пидора ответ'

    def start(self) -> ResponseMessage:
        answer = "Шлюхи аргумент"
        return ResponseMessage(ResponseMessageItem(text=answer))

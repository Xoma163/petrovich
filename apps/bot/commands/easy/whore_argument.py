from apps.bot.classes.command import Command
from apps.bot.classes.event import Event
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class WhoreArgument(Command):
    name = "шлюхи"
    suggest_for_similar = False
    non_mentioned = True

    def accept(self, event: Event) -> bool:
        return event.message and event.message.clear == 'шлюхи аргумент'

    def start(self) -> ResponseMessage:
        answer = "Аргумент не нужен, пидор обнаружен"
        return ResponseMessage(ResponseMessageItem(text=answer))

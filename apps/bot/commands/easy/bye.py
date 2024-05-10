from apps.bot.classes.command import Command
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import random_event


class Bye(Command):
    name = "пока"
    names = ["бай", "bb", "бай-бай", "байбай", "бб", "досвидос", "бывай", 'пока-пока', 'пока((']
    mentioned = True

    def start(self) -> ResponseMessage:
        answer = random_event(self.full_names)
        return ResponseMessage(ResponseMessageItem(text=answer))

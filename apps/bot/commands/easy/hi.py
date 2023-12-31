from apps.bot.classes.command import Command
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import random_event


class Hi(Command):
    name = "привет"
    names = ["хай", "даров", "дарова", "здравствуй", "здравствуйте", "привки", "прив", "q", "qq", "ку",
             "куку", "здаров", "здарова", "хеей", "хало", "hi", "hello", 'салам']
    mentioned = True

    def start(self) -> ResponseMessage:
        answer = random_event(self.full_names)
        answer = self.bot.get_quote_text(answer)
        return ResponseMessage(ResponseMessageItem(text=answer))

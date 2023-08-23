from apps.bot.classes.Command import Command
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import random_event


class Hi(Command):
    name = "привет"
    names = ["хай", "даров", "дарова", "здравствуй", "здравствуйте", "привки", "прив", "q", "qq", "ку",
             "куку", "здаров", "здарова", "хеей", "хало", "hi", "hello", 'салам']
    mentioned = True

    def start(self):
        answer = random_event(self.full_names)
        return ResponseMessage(
            ResponseMessageItem(
                text=answer,
                peer_id=self.event.peer_id,
                message_thread_id=self.event.message_thread_id
            )
        )

from apps.bot.classes.Command import Command
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import random_event


class Clear(Command):
    name = "ясно"
    names = ["ммм"]
    suggest_for_similar = False
    non_mentioned = True

    def start(self):
        if self.event.message.command == 'ммм':
            answer = random_event(["Данон", "Хуета"])
        else:
            answer = "Хуета"

        return ResponseMessage(
            ResponseMessageItem(
                text=answer,
                peer_id=self.event.peer_id,
                message_thread_id=self.event.message_thread_id
            )
        )

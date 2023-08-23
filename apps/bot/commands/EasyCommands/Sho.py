from apps.bot.classes.Command import Command
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem


class Sho(Command):
    name = "шо"
    names = ["шоты", "тышо"]
    suggest_for_similar = False
    non_mentioned = True

    def start(self):
        answer = "я нишо а ты шо"

        return ResponseMessage(
            ResponseMessageItem(
                text=answer,
                peer_id=self.event.peer_id,
                message_thread_id=self.event.message_thread_id
            )
        )

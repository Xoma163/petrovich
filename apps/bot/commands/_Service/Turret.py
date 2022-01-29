from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import TURETT_WORDS
from apps.bot.utils.utils import random_probability, random_event


class Turett(Command):
    conversation = True
    priority = 85

    def accept(self, event):
        if event.chat and event.chat.need_turett:
            chance = 50 if event.chat.mentioning else 2
            if random_probability(chance):
                msg = random_event(TURETT_WORDS)
                event.bot.parse_and_send_msgs(msg, event.peer_id)
        return False

    def start(self):
        pass

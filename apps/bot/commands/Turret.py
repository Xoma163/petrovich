from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import TURRET_WORDS
from apps.bot.utils.utils import random_probability, random_event


class Turret(Command):
    conversation = True

    def accept(self, event):
        if event.chat and event.chat.need_turret and random_probability(5):
            msg = random_event(TURRET_WORDS)
            event.bot.parse_and_send_msgs(event.peer_id, msg)
        return False

    def start(self):
        pass

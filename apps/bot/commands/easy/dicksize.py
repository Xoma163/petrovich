import datetime

import numpy as np

from apps.bot.classes.command import Command
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class DickSize(Command):
    name = "член"

    mentioned = True
    hidden = True
    suggest_for_similar = False

    def start(self) -> ResponseMessage:
        seed = int(datetime.datetime.now().strftime("%d%m%Y")) + self.event.sender.pk
        size = np.random.default_rng(seed=seed).normal(10, 2.2) + 3.21
        size = round(size, 1)
        answer = f"Ваш член сегодня - {size}см"
        return ResponseMessage(ResponseMessageItem(text=answer))

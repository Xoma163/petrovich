import datetime

import numpy as np

from apps.bot.classes.command import Command
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class DickSize(Command):
    name = "член"

    mentioned = True

    def start(self) -> ResponseMessage:
        seed = int(datetime.datetime.now().strftime("%d%m%Y")) + self.event.sender.pk
        size = np.random.default_rng(seed=seed).normal(10, 2.2) + 3.21
        size = round(size, 1)

        if self.event.is_from_chat:
            button = self.bot.get_button("Член", self.name)
            keyboard = self.bot.get_inline_keyboard([button])
            answer = f"{self.event.sender.name}, ваш член сегодня - {size}см"
        else:
            keyboard = None
            answer = f"Ваш член сегодня - {size}см"
        return ResponseMessage(ResponseMessageItem(text=answer, keyboard=keyboard))

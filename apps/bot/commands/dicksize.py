import datetime

import numpy as np

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform
from apps.bot.classes.const.exceptions import PSkip
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class DickSize(Command):
    name = "член"

    mentioned = True

    platforms = [Platform.TG]

    def start(self) -> ResponseMessage:
        self.bot: TgBot

        seed = int(datetime.datetime.now().strftime("%d%m%Y")) + self.event.sender.pk
        size = np.random.default_rng(seed=seed).normal(10, 2.2) + 3.21
        size = round(size, 1)

        message_id = None
        keyboard = None

        if self.event.is_from_chat:
            button = self.bot.get_button("Член", self.name)
            keyboard = self.bot.get_inline_keyboard([button])
            answer = f"{self.event.sender.name}, ваш член сегодня - {size}см"

            if message := self.event.raw.get('callback_query', {}).get('message', {}):
                dicks = message['text']
                if answer not in dicks:
                    answer = f"{dicks}\n{answer}"
                    message_id = message['message_id']
                else:
                    raise PSkip()
        else:
            answer = f"Ваш член сегодня - {size}см"
        return ResponseMessage(ResponseMessageItem(text=answer, keyboard=keyboard, message_id=message_id))

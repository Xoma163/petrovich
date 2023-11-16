import re
from datetime import datetime

import numpy as np

from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform
from apps.bot.classes.const.exceptions import PSkip
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class DickSize(Command):
    name = "член"
    mentioned = True
    platforms = [Platform.TG]

    def start(self) -> ResponseMessage:
        if self.event.is_from_pm:
            answer = f"Ваш член сегодня - {self.get_dick_size()}см"
            return ResponseMessage(ResponseMessageItem(text=answer))

        button = self.bot.get_button("Член", self.name)
        keyboard = self.bot.get_inline_keyboard([button])
        answer = f"Максим, ваш член сегодня - 8.6см"

        # Не была нажата кнопка
        message = self.event.raw.get('callback_query', {}).get('message', {})
        if not message:
            return ResponseMessage(ResponseMessageItem(text=answer, keyboard=keyboard))

        message_id = None
        dicks = message['text']
        today_message = datetime.fromtimestamp(message['date']).date() == datetime.now().date()
        if today_message:
            if answer not in dicks:
                answer = f"{dicks}\n{answer}"
                message_id = message['message_id']
            else:
                raise PSkip()
        answer = self.sort_message(answer)
        return ResponseMessage(ResponseMessageItem(text=answer, keyboard=keyboard, message_id=message_id))

    def get_dick_size(self) -> float:
        seed = int(datetime.now().strftime("%d%m%Y")) + self.event.sender.pk
        size = np.random.default_rng(seed=seed).normal(10, 2.2) + 3.21
        return round(size, 1)

    @staticmethod
    def sort_message(message: str):
        dicksize_re = re.compile(r"(.*),.*- (.*)см")
        dicks = re.findall(dicksize_re, message)
        sorted_dicks = list(sorted(dicks, key=lambda x: float(x[1])))
        answer = "\n".join([f"{dick[0]}, ваш член сегодня - {dick[1]}см" for dick in sorted_dicks])
        return answer

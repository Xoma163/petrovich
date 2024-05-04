import requests
from bs4 import BeautifulSoup

from apps.bot.classes.command import Command
from apps.bot.classes.help_text import HelpText
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import random_event


class Sin(Command):
    name = "грех"

    help_text = HelpText(
        commands_text="присылает случайный грех"
    )

    URL = "https://pravera.ru/index/spisok_grekhov_dlja_ispovedi_podgotovka_v_pravoslavii/0-2381"

    def start(self) -> ResponseMessage:
        sins = self.get_sins()
        answer = random_event(sins)
        button = self.bot.get_button("Ещё", self.name)
        keyboard = self.bot.get_inline_keyboard([button])
        return ResponseMessage(ResponseMessageItem(text=answer, keyboard=keyboard))

    def get_sins(self) -> list[str]:
        r = requests.get(self.URL, verify=False)
        bs4 = BeautifulSoup(r.content)
        sins = bs4.select(".main-table p")[10].text.split('\n')
        return sins

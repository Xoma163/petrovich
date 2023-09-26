from apps.bot.classes.command import Command
from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import random_event
from petrovich.settings import STATIC_ROOT


class HappyNewYear(Command):
    name = "с"
    names = ["с"]
    suggest_for_similar = False
    enabled = False

    def accept(self, event: Event) -> bool:
        hny_phrases = [
            'с новым годом', "с нг", "с наступающим", "с наступающими", "с наступающим новым годом", "с н г", "снг",
            "с праздником", "с наступающими праздниками"
        ]
        return event.message and any([hny_phrase in event.message.clear for hny_phrase in hny_phrases])

    def start(self) -> ResponseMessage:
        messages = [
            ResponseMessageItem(text="И ваc тоже, и вам тогоже"),
            ResponseMessageItem(text="УРААААААААААА"),
            [
                ResponseMessageItem(text="ННОООООВВЫЫЫЫЙ ГОД К НАМ МЧИТСЯ"),
                ResponseMessageItem(text="СКООООРААА ВСЁ СЛУЧИТСЯ"),
                ResponseMessageItem(text="СБУУДЕТСЯ ЧТО СНИТСЯ"),
                ResponseMessageItem(text="ЧТО ОПЯТЬ НАС ОБМАНУТ, НИЧЕГО НЕ ДАДУТ"),
                ResponseMessageItem(text="https://youtu.be/xviBEvbxgZ0", attachments=[
                    self.bot.get_photo_attachment(f"{STATIC_ROOT}/bot/img/sng.jpg", peer_id=self.event.peer_id,
                                                  filename="petrovich_hny.jpg")])
            ],
            ResponseMessageItem(text="https://youtu.be/8PzPHKGpNXs"),
            ResponseMessageItem(text="https://youtu.be/pESX7mQwTNU")
        ]
        rmis = random_event(messages)
        return ResponseMessage(rmis)

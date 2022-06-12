from apps.bot.classes.Command import Command
from apps.bot.utils.utils import random_event
from petrovich.settings import STATIC_ROOT


class HappyNewYear(Command):
    name = "с"
    names = ["с"]
    suggest_for_similar = False
    enabled = False

    def accept(self, event):
        hny_phrases = [
            'с новым годом', "с нг", "с наступающим", "с наступающими", "с наступающим новым годом", "с н г", "снг",
            "с праздником", "с наступающими праздниками"
        ]
        return event.message and any([hny_phrase in event.message.clear for hny_phrase in hny_phrases])

    def start(self):
        answers = [
            "И ваc тоже, и вам тогоже",
            "УРААААААААААА",
            [
                "ННОООООВВЫЫЫЫЙ ГОД К НАМ МЧИТСЯ",
                "СКООООРААА ВСЁ СЛУЧИТСЯ",
                "СБУУДЕТСЯ ЧТО СНИТСЯ",
                "ЧТО ОПЯТЬ НАС ОБМАНУТ, НИЧЕГО НЕ ДАДУТ",
                "https://youtu.be/xviBEvbxgZ0"
            ],
            {'attachments': self.bot.upload_photo(f"{STATIC_ROOT}/bot/img/sng.jpg", peer_id=self.event.peer_id)},
            "https://youtu.be/8PzPHKGpNXs",
            "https://youtu.be/pESX7mQwTNU"
        ]
        answer = random_event(answers)
        return answer

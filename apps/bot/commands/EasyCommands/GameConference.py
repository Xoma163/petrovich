from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand


class GameConference(CommonCommand):
    name = "игровая"
    names = ["ставошная"]
    help_text = "ссылка-приглашение в игровую конфу"
    platforms = [Platform.VK]

    def start(self):
        return 'https://vk.me/join/AJQ1d9ppmRflxVoEplfcaUHv'

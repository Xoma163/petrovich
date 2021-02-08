from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand


# ToDo: TG игровая конфа
class GameConference(CommonCommand):
    names = ["игровая", "ставошная"]
    help_text = "Игровая - ссылка-приглашение в игровую конфу"
    platforms = [Platform.VK]

    def start(self):
        return 'https://vk.me/join/AJQ1d9ppmRflxVoEplfcaUHv'

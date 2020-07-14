from apps.bot.classes.common.CommonCommand import CommonCommand


# ToDo: TG игровая конфа
class GameConference(CommonCommand):
    def __init__(self):
        names = ["игровая", "ставошная"]
        help_text = "Игровая - ссылка-приглашение в игровую конфу"
        super().__init__(names, help_text, platforms=['vk'])

    def start(self):
        return 'https://vk.me/join/AJQ1d9ppmRflxVoEplfcaUHv'

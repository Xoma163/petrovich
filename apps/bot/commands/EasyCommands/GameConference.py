from apps.bot.classes.common.CommonCommand import CommonCommand


class GameConference(CommonCommand):
    def __init__(self):
        names = ["игровая", "ставошная"]
        help_text = "Игровая - ссылка-приглашение в игровую конфу"
        # ToDo: conference for tg
        super().__init__(names, help_text, enabled=False)

    def start(self):
        return 'https://vk.me/join/AJQ1d9ppmRflxVoEplfcaUHv'

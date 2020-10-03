from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand


class Diary(CommonCommand):
    def __init__(self):
        names = ["ежедневник"]
        help_text = "Ежедневник - ссылка на ежедневник"
        super().__init__(names, help_text, access=Role.TRUSTED)

    def start(self):
        url = 'https://diary.andrewsha.net/'
        return {'msg': url, 'attachments': [url]}

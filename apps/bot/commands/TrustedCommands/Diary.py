from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand


class Diary(CommonCommand):
    names = "ежедневник"
    help_text = "Ежедневник - ссылка на ежедневник"
    access = Role.TRUSTED
    suggest_for_similar = False

    def start(self):
        url = 'https://diary.andrewsha.net/'
        return {'msg': url, 'attachments': [url]}

from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand


class Discord(CommonCommand):
    names = ["дискорд", "диск"]
    help_text = "Дискорд - ссылка на канал в дискорде"
    access = Role.TRUSTED

    def start(self):
        url = 'https://discord.gg/kYGSNzv'
        return {'msg': url, 'attachments': [url]}

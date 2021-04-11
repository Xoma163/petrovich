from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand


class Discord(CommonCommand):
    name = "дискорд"
    names = ["диск"]
    help_text = "ссылка на канал в дискорде"
    access = Role.TRUSTED

    def start(self):
        url = 'https://discord.gg/kYGSNzv'
        return {'msg': url, 'attachments': [url]}

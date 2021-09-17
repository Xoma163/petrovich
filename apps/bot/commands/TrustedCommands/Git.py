from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand


class Git(CommonCommand):
    name = "гит"
    names = ["гитхаб"]
    help_text = "ссылка на гитхаб"
    access = Role.TRUSTED

    def start(self):
        url = 'https://github.com/Xoma163/petrovich/'
        return {'msg': url, 'attachments': [url]}

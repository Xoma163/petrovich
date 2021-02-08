from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand


class Git(CommonCommand):
    names = ["гит", "гитхаб"]
    help_text = "Гит - ссылка на гитхаб"
    access = Role.TRUSTED


    def start(self):
        url = 'https://github.com/Xoma163/petrovich/'
        return {'msg': url, 'attachments': [url]}

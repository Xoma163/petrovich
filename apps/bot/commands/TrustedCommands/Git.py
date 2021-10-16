from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.Command import Command


class Git(Command):
    name = "гит"
    names = ["гитхаб"]
    help_text = "ссылка на гитхаб"
    access = Role.TRUSTED

    def start(self):
        url = 'https://github.com/Xoma163/petrovich/'
        return {'msg': url, 'attachments': [url]}

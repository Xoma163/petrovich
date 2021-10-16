from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role


class Git(Command):
    name = "гит"
    names = ["гитхаб"]
    help_text = "ссылка на гитхаб"
    access = Role.TRUSTED

    def start(self):
        url = 'https://github.com/Xoma163/petrovich/'
        return {'text': url, 'attachments': [url]}

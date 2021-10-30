from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role, Platform


class Git(Command):
    name = "гит"
    names = ["гитхаб"]
    help_text = "ссылка на гитхаб"
    access = Role.TRUSTED

    def start(self):
        url = 'https://github.com/Xoma163/petrovich/'

        if self.event.platform == Platform.TG:
            return {'text': f"[Гитхаб]({url})",'parse_mode':'markdown'}
        return url

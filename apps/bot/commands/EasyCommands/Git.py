from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform


class Git(Command):
    name = "гит"
    names = ["гитхаб"]
    name_tg = 'github'

    help_text = "ссылка на гитхаб"

    def start(self):
        url = 'https://github.com/Xoma163/petrovich/'

        if self.event.platform == Platform.TG:
            return {'text': f"[Гитхаб]({url})", 'parse_mode': 'markdown'}
        return url

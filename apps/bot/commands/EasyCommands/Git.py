from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.utils.utils import get_tg_formatted_url


class Git(Command):
    name = "гит"
    names = ["гитхаб"]
    name_tg = 'github'

    help_text = "ссылка на гитхаб"

    def start(self):
        url = 'https://github.com/Xoma163/petrovich/'

        if self.event.platform == Platform.TG:
            url = get_tg_formatted_url("Гитхаб", url)
        return url

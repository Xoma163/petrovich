from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.utils.utils import get_tg_formatted_url


class Documentation(Command):
    name = "документация"
    names = ["дока"]
    help_text = "ссылка на документацию"

    def start(self):
        url = 'https://github.com/Xoma163/petrovich/wiki/1.1-Документация-для-пользователей'
        if self.event.platform == Platform.TG:
            url = get_tg_formatted_url("Документация", url)
        return url

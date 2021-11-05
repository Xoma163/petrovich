from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.utils.utils import get_tg_formatted_url


class Diary(Command):
    name = "ежедневник"
    help_text = "ссылка на ежедневник"
    access = Role.TRUSTED
    suggest_for_similar = False

    def start(self):
        url = 'https://diary.andrewsha.net/'

        if self.event.platform == Platform.TG:
            url = get_tg_formatted_url("Ежедневник", url)
        return url

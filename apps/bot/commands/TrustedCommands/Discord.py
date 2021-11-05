from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.utils.utils import get_tg_formatted_url


class Discord(Command):
    name = "дискорд"
    names = ["диск"]
    name_tg = 'discord'

    help_text = "ссылка на канал в дискорде"

    access = Role.TRUSTED

    def start(self):
        url = 'https://discord.gg/kYGSNzv'

        if self.event.platform == Platform.TG:
            url = get_tg_formatted_url("Дискорд", url)
        return url

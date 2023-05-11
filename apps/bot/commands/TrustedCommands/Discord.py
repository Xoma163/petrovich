from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role


class Discord(Command):
    name = "дискорд"
    names = ["диск"]
    name_tg = 'discord'

    help_text = "ссылка на канал в дискорде"

    access = Role.TRUSTED

    def start(self):
        url = 'https://discord.gg/kYGSNzv'
        return self.bot.get_formatted_url("Дискорд", url)

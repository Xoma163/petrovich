from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role


class Discord(Command):
    name = "дискорд"
    names = ["диск"]
    help_text = "ссылка на канал в дискорде"
    access = Role.TRUSTED

    def start(self):
        return 'https://discord.gg/kYGSNzv'

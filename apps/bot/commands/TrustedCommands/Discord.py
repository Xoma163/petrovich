from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role, Platform


class Discord(Command):
    name = "дискорд"
    names = ["диск"]
    help_text = "ссылка на канал в дискорде"
    access = Role.TRUSTED

    def start(self):
        url = 'https://discord.gg/kYGSNzv'

        if self.event.platform == Platform.TG:
            return {'text': f"[Ежедневник]({url})"}
        return url

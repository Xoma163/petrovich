from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role


class Diary(Command):
    name = "ежедневник"
    help_text = "ссылка на ежедневник"
    access = Role.TRUSTED
    suggest_for_similar = False

    def start(self):
        url = 'https://diary.andrewsha.net/'
        return {'text': url, 'attachments': [url]}

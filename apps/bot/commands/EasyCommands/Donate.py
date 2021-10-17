from apps.bot.classes.Command import Command
from petrovich.settings import STATIC_ROOT


class Donate(Command):
    name = "донат"
    help_text = "ссылка на донат"

    def start(self):
        url = 'https://www.donationalerts.com/r/xoma163'
        attachments = self.bot.upload_photos(f"{STATIC_ROOT}/bot/img/donate.jpg")
        return {'text': url, 'attachments': attachments}

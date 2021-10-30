from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from petrovich.settings import STATIC_ROOT


class Donate(Command):
    name = "донат"
    help_text = "ссылка на донат"

    def start(self):
        url = 'https://www.donationalerts.com/r/xoma163'
        attachments = self.bot.upload_photos(f"{STATIC_ROOT}/bot/img/donate.jpg", peer_id=self.event.peer_id)
        if self.event.platform == Platform.TG:
            return {'text': f"[Задонатить]({url})", 'attachments': attachments}
        return {'text': url, 'attachments': attachments}

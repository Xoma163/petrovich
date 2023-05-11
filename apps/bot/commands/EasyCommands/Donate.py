from apps.bot.classes.Command import Command
from petrovich.settings import STATIC_ROOT


class Donate(Command):
    name = "донат"
    name_tg = 'donate'
    help_text = "ссылка на донат"

    def start(self):
        url = 'https://www.donationalerts.com/r/xoma163'
        attachment = self.bot.get_photo_attachment(
            f"{STATIC_ROOT}/bot/img/donate.jpg",
            peer_id=self.event.peer_id,
            filename="petrovich_donate.jpg"
        )
        return {'text': self.bot.get_formatted_url("Задонатить", url), 'attachments': attachment}

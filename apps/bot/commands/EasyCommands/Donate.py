from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.utils.utils import get_tg_formatted_url
from petrovich.settings import STATIC_ROOT


class Donate(Command):
    name = "донат"
    name_tg = 'donate'
    help_text = "ссылка на донат"

    def start(self):
        url = 'https://www.donationalerts.com/r/xoma163'
        attachment = self.bot.upload_photo(f"{STATIC_ROOT}/bot/img/donate.jpg", peer_id=self.event.peer_id)
        if self.event.platform == Platform.TG:
            return {'text': get_tg_formatted_url("Задонатить", url), 'attachments': attachment}
        return {'text': url, 'attachments': attachment}

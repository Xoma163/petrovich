from apps.bot.classes.common.CommonCommand import CommonCommand
from petrovich.settings import STATIC_ROOT


class Donate(CommonCommand):
    name = "донат"
    help_text = "ссылка на донат"

    def start(self):
        url = 'https://www.donationalerts.com/r/xoma163'
        attachments = self.bot.upload_photos(f"{STATIC_ROOT}/bot/img/donate.jpg")
        attachments.append(url)
        return {'msg': url, 'attachments': attachments}

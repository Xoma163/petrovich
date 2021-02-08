from apps.bot.classes.common.CommonCommand import CommonCommand
from petrovich.settings import STATIC_DIR


class Donate(CommonCommand):
    names = ["донат"]
    help_text = "Донат - ссылка на донат"

    def start(self):
        url = 'https://www.donationalerts.com/r/xoma163'
        attachments = self.bot.upload_photos(f"{STATIC_DIR}/bot/img/donate.jpg")
        attachments.append(url)
        return {'msg': url, 'attachments': attachments}

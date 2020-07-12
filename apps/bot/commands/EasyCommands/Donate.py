from apps.bot.classes.common.CommonCommand import CommonCommand
from petrovich.settings import BASE_DIR


class Donate(CommonCommand):
    def __init__(self):
        names = ["донат"]
        help_text = "Донат - ссылка на донат"
        super().__init__(names, help_text)

    def start(self):
        url = 'https://www.donationalerts.com/r/xoma163'
        attachments = self.bot.upload_photos(f"{BASE_DIR}/static/bot/img/donate.jpg")
        attachments.append(url)
        return {'msg': url, 'attachments': attachments}

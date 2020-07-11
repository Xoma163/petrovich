from apps.bot.classes.common.CommonCommand import CommonCommand


class Donate(CommonCommand):
    def __init__(self):
        names = ["донат"]
        help_text = "Донат - ссылка на донат"
        # ToDo: TG
        super().__init__(names, help_text, enabled=False)

    def start(self):
        attachment = self.bot.get_attachment_by_id('photo', None, 457243301)
        url = 'https://www.donationalerts.com/r/xoma163'
        return {'msg': url, 'attachments': [attachment, url]}

from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.events.TgEvent import TgEvent
from apps.bot.classes.events.VkEvent import VkEvent


class Donate(CommonCommand):
    def __init__(self):
        names = ["донат"]
        help_text = "Донат - ссылка на донат"
        super().__init__(names, help_text)

    # ToDo: photo for TG
    def start(self):
        url = 'https://www.donationalerts.com/r/xoma163'

        if isinstance(self.event, VkEvent):
            attachment = self.bot.get_attachment_by_id('photo', None, 457243301)
            return {'msg': url, 'attachments': [attachment, url]}
        elif isinstance(self.event, TgEvent):
            return {'msg': url,
                    'attachments': ['https://coub.com/view/2g7hmu']}
            # return url

from apps.bot.classes.messages.attachments.Attachment import Attachment


class StickerAttachment(Attachment):
    TYPE = 'sticker'

    def __init__(self):
        super().__init__(self.TYPE)
        self.width = None
        self.height = None
        self.emoji = None
        self.animated = False

    def parse_vk(self, event):
        for image in event['images']:
            if image['height'] == 128:
                self.width = image['width']
                self.height = image['height']
                self.url = image['url']
                break

    def parse_tg(self, event, tg_bot):
        attrs = ['width', 'height', 'file_id', 'file_size', 'emoji']
        for attr in attrs:
            setattr(self, attr, event.get(attr, None))
        self.animated = event['is_video'] or event['is_animated']

        self.set_private_download_url_tg(tg_bot, self.file_id)

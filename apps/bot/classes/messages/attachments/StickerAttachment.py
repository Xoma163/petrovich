from apps.bot.classes.messages.attachments.Attachment import Attachment


class StickerAttachment(Attachment):

    def __init__(self):
        super().__init__('sticker')
        self.width = None
        self.height = None
        self.emoji = None
        self.animated = False

    def parse_vk_sticker(self, event_sticker):
        for image in event_sticker['images']:
            if image['height'] == 128:
                self.width = image['width']
                self.height = image['height']
                self.url = image['url']
                break

    def parse_tg_sticker(self, sticker, tg_bot):
        attrs = ['width', 'height', 'file_id', 'file_size', 'emoji']
        for attr in attrs:
            setattr(self, attr, sticker[attr])
        self.animated = sticker['is_video'] or sticker['is_animated']

        self.set_private_download_url_tg(tg_bot, self.file_id)

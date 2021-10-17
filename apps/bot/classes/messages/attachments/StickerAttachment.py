from apps.bot.classes.messages.attachments.Attachment import Attachment


class StickerAttachment(Attachment):

    def __init__(self):
        super().__init__()
        self.width = None
        self.height = None

    def parse_vk_sticker(self, event_sticker):
        for image in event_sticker['images']:
            if image['height'] == 128:
                self.width = image['width']
                self.height = image['height']
                self.url = image['url']
                break

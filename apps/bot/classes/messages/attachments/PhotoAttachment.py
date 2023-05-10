from apps.bot.classes.messages.attachments.Attachment import Attachment


class PhotoAttachment(Attachment):
    TYPE = "photo"

    def __init__(self):
        super().__init__(self.TYPE)
        self.width = None
        self.height = None

    def parse_tg(self, event, tg_bot):
        self.width = event.get('width')
        self.height = event.get('height')
        self.size = event['file_size']

        self.file_id = event['file_id']
        self.set_private_download_url_tg(tg_bot, self.file_id)

    def parse_vk(self, event):
        max_size_photo = sorted(event['sizes'], key=lambda x: x['height'])[-1]
        self.width = max_size_photo['width']
        self.height = max_size_photo['height']
        self.public_download_url = max_size_photo['url']

    def parse_api(self, event):
        self.public_download_url = event.get('url')

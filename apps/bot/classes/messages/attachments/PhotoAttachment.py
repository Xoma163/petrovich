from apps.bot.classes.messages.attachments.Attachment import Attachment


class PhotoAttachment(Attachment):

    def __init__(self):
        super().__init__()
        self.width = None
        self.height = None

    def parse_tg_photo(self, event_photo, tg_bot):
        self.width = event_photo.get('width')
        self.height = event_photo.get('height')
        self.size = event_photo['file_size']

        file_id = event_photo['file_id']
        self.set_private_download_url_tg(tg_bot, file_id)

    def parse_vk_photo(self, event_photo):
        max_size_photo = sorted(event_photo['sizes'], key=lambda x: x['height'])[-1]
        self.width = max_size_photo['width']
        self.height = max_size_photo['height']
        self.public_download_url = max_size_photo['url']

import requests

from apps.bot.classes.messages.attachments.Attachment import Attachment


class PhotoAttachment(Attachment):

    def __init__(self):
        super().__init__('photo')
        self.width = None
        self.height = None

    def parse_tg_photo(self, event_photo, tg_bot):
        self.width = event_photo.get('width')
        self.height = event_photo.get('height')
        self.size = event_photo['file_size']

        file_id = event_photo['file_id']
        self.set_private_download_url_tg(tg_bot, file_id)

    def download_content(self):
        self.content = requests.get(self.private_download_url).content
        return self.content

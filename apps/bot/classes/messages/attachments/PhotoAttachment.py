from apps.bot.classes.messages.attachments.Attachment import Attachment


class PhotoAttachment(Attachment):
    TYPE = "photo"

    def __init__(self):
        super().__init__(self.TYPE)
        self.width = None
        self.height = None

    def parse_tg(self, event):
        self.width = event.get('width')
        self.height = event.get('height')
        self.size = event['file_size']

        self.file_id = event['file_id']

    def parse_api(self, event):
        self.public_download_url = event.get('url')

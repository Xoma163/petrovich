import base64

from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.messages.attachments.attachment import Attachment
from apps.bot.classes.messages.attachments.mixins.sized_mixin import SizedMixin


class PhotoAttachment(Attachment, SizedMixin):
    TYPE = "photo"

    def __init__(self):
        super().__init__(self.TYPE)
        self.activity = ActivitiesEnum.UPLOAD_PHOTO

    def parse_tg(self, event):
        self.width = event.get('width')
        self.height = event.get('height')
        self.size = event['file_size']

        self.file_id = event['file_id']

    def parse_api(self, event):
        self.public_download_url = event.get('url')

    def base64(self) -> base64:
        self.download_content()
        return base64.b64encode(self.content).decode('utf-8')

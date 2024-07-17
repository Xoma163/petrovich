import logging

from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.messages.attachments.attachment import Attachment

logger = logging.getLogger()


class DocumentMimeType:
    def __init__(self, _type: str):
        self.type = _type

    @property
    def is_image(self):
        return self._check_value('image')

    @property
    def is_text(self):
        return self._check_value('text')

    @property
    def is_audio(self):
        return self._check_value('audio')

    def _check_value(self, _type):
        return self.type.startswith(f'{_type}/')


class DocumentAttachment(Attachment):
    TYPE = 'document'
    ACTIVITY = ActivitiesEnum.UPLOAD_DOCUMENT

    def __init__(self):
        super().__init__(self.TYPE)

        self.mime_type: DocumentMimeType | None = None

    def parse_tg(self, event):
        self.file_id = event['file_id']
        self.file_name_full = event.get('file_name')
        try:
            self.file_name, self.ext = event['file_name'].rsplit('.', 1)
        except:
            self.file_name = event.get('file_name')
        self.mime_type = DocumentMimeType(event['mime_type'])
    def read_text(self):
        return self.download_content().decode('utf-8')

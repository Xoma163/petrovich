import logging

from apps.bot.core.chat_actions import ChatActionEnum
from apps.bot.core.messages.attachments.attachment import Attachment
from apps.bot.core.messages.attachments.mixins.thumbnail_mixin import ThumbnailMixin
from apps.shared.exceptions import PWarning

logger = logging.getLogger()


class DocumentMimeType:
    def __init__(self, _type: str):
        self.type = _type

    def __str__(self):
        return self.type

    @property
    def is_image(self):
        return self._check_value('image/')

    @property
    def is_text(self):
        return self._check_value('text/')

    @property
    def is_pdf(self):
        return self._check_value('application/pdf')

    @property
    def is_audio(self):
        return self._check_value('audio/')

    def _check_value(self, _type):
        return self.type.startswith(f'{_type}')


class DocumentAttachment(Attachment, ThumbnailMixin):
    TYPE = 'document'
    ACTIVITY = ChatActionEnum.UPLOAD_DOCUMENT

    def __init__(self):
        super().__init__(self.TYPE)

        self.mime_type: DocumentMimeType | None = None

    def parse_tg(self, event):
        super().parse_tg(event)

        self.mime_type = DocumentMimeType(event['mime_type'])

    def read_text(self):
        content = self.download_content()
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            raise PWarning("Не могу прочитать файл. Убедитесь, что кодировка файла UTF-8")

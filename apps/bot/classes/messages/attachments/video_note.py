from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.messages.attachments.attachment import Attachment
from apps.bot.classes.messages.attachments.photo import PhotoAttachment


class VideoNoteAttachment(Attachment):
    TYPE = 'video_note'

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration: float | None = None  # sec
        self.activity = ActivitiesEnum.UPLOAD_VIDEO_NOTE
        self.ext: str = 'oga'
        self.file_name: str = 'Кружочек'
        self.file_name_full = f'{self.file_name}.{self.ext}'

        self.thumbnail_url: str | None = None
        self.thumbnail: PhotoAttachment | None = None

    def parse_tg(self, event):
        self.duration = event.get('duration')
        self.name = event.get('name')
        self.size = event['file_size']

        self.file_id = event['file_id']

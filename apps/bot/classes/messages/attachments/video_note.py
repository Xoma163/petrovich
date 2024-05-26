from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.messages.attachments.attachment import Attachment


class VideoNoteAttachment(Attachment):
    TYPE = 'video_note'

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration: float | None = None  # sec
        self.thumb = None
        self.activity = ActivitiesEnum.UPLOAD_VIDEO_NOTE
        self.ext = 'oga'
        self.file_name = 'Кружочек'
        self.file_name_full = f'{self.file_name}.{self.ext}'

    def parse_tg(self, event):
        self.duration = event.get('duration')
        self.name = event.get('name')
        self.size = event['file_size']

        self.file_id = event['file_id']

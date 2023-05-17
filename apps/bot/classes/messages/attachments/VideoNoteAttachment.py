from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.messages.attachments.Attachment import Attachment


class VideoNoteAttachment(Attachment):
    TYPE = 'video_note'

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration = None  # sec
        self.thumb: str = None
        self.activity = ActivitiesEnum.UPLOAD_VIDEO_NOTE

    def parse_tg(self, event):
        self.duration = event.get('duration')
        self.name = event.get('name')
        self.size = event['file_size']

        self.file_id = event['file_id']

from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.messages.attachments.attachment import Attachment


class VideoAttachment(Attachment):
    TYPE = 'video'

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration = None  # sec
        self.width = None
        self.height = None
        self.thumb = None
        self.activity = ActivitiesEnum.UPLOAD_VIDEO

        self.m3u8_url = None

    def parse_tg(self, event):
        self.duration = event.get('duration')
        self.width = event.get('width')
        self.height = event.get('height')
        self.name = event.get('name')
        self.size = event['file_size']

        self.file_id = event['file_id']

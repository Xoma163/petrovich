from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.messages.attachments.attachment import Attachment
from apps.bot.classes.messages.attachments.photo import PhotoAttachment


class VideoAttachment(Attachment):
    TYPE = 'video'

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration: int | None = None  # sec
        self.width: int | None = None
        self.height: int | None = None
        self.thumbnail_url: str | None = None
        self.thumbnail: PhotoAttachment | None = None
        self.activity = ActivitiesEnum.UPLOAD_VIDEO

        self.m3u8_url = None

    def parse_tg(self, event):
        self.duration = event.get('duration')
        self.width = event.get('width')
        self.height = event.get('height')
        self.name = event.get('name')
        self.size = event['file_size']

        self.file_id = event['file_id']

    def set_thumbnail(self):
        from apps.bot.utils.utils import center_with_blur_background

        if self.thumbnail_url is None:
            return
        thumb_file = PhotoAttachment()
        thumb_file.parse(self.thumbnail_url, guarantee_url=True)
        thumbnail = center_with_blur_background(thumb_file)
        thumbnail_att = PhotoAttachment()
        thumbnail_att.parse(thumbnail)
        self.thumbnail = thumbnail_att

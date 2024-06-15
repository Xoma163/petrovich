from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.messages.attachments.attachment import Attachment
from apps.bot.classes.messages.attachments.photo import PhotoAttachment


class AudioAttachment(Attachment):
    TYPE = "audio"

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration: float | None = None

        self.artist: str | None = None
        self.title: str | None = None

        self.thumbnail_url: str | None = None
        self.thumbnail: PhotoAttachment | None = None
        self.activity = ActivitiesEnum.UPLOAD_AUDIO

    def parse_tg(self, event):
        self.duration = event.get('duration')
        self.size = event['file_size']

        self.file_id = event['file_id']
        self.filename_full = event.get('file_name')
        try:
            self.file_name, self.ext = event['file_name'].rsplit('.', 1)
        except:
            self.file_name = event.get('file_name')
            if event['mime_type'] == 'audio/mpeg':
                self.ext = 'mp3'

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

from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.messages.attachments.attachment import Attachment
from apps.bot.classes.messages.attachments.mixins.duration_mixin import DurationMixin
from apps.bot.classes.messages.attachments.mixins.thumbnail_mixin import ThumbnailMixin


class AudioAttachment(Attachment, ThumbnailMixin, DurationMixin):
    TYPE = "audio"
    ACTIVITY = ActivitiesEnum.UPLOAD_AUDIO

    def __init__(self):
        super().__init__(self.TYPE)
        self.artist: str | None = None
        self.title: str | None = None

    def parse_tg(self, event):
        self.duration = event.get('duration')
        self.size = event['file_size']

        self.file_id = event['file_id']
        if event['mime_type'] == 'audio/mpeg':
            self.ext = 'mp3'

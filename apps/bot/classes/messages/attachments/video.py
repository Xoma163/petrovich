from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.messages.attachments.attachment import Attachment
from apps.bot.classes.messages.attachments.mixins.duration_mixin import DurationMixin
from apps.bot.classes.messages.attachments.mixins.sized_mixin import SizedMixin
from apps.bot.classes.messages.attachments.mixins.thumbnail_mixin import ThumbnailMixin


class VideoAttachment(Attachment, ThumbnailMixin, SizedMixin, DurationMixin):
    TYPE = 'video'

    def __init__(self):
        super().__init__(self.TYPE)
        self.activity = ActivitiesEnum.UPLOAD_VIDEO

        self.m3u8_url = None

    def parse_tg(self, event):
        self.duration = event.get('duration')
        self.width = event.get('width')
        self.height = event.get('height')
        self.name = event.get('name')
        self.size = event['file_size']

        self.file_id = event['file_id']

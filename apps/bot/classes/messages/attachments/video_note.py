from apps.bot.classes.messages.attachments.attachment import Attachment
from apps.bot.classes.messages.attachments.mixins.duration_mixin import DurationMixin
from apps.bot.classes.messages.attachments.mixins.thumbnail_mixin import ThumbnailMixin


class VideoNoteAttachment(Attachment, DurationMixin, ThumbnailMixin):
    TYPE = 'video_note'

    def __init__(self):
        super().__init__(self.TYPE)

    def parse_tg(self, event):
        self.duration = event.get('duration')
        self.size = event['file_size']
        self.file_id = event['file_id']

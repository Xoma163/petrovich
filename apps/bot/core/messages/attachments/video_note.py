from apps.bot.core.messages.attachments.attachment import Attachment
from apps.bot.core.messages.attachments.mixins.duration_mixin import DurationMixin
from apps.bot.core.messages.attachments.mixins.thumbnail_mixin import ThumbnailMixin


class VideoNoteAttachment(Attachment, DurationMixin, ThumbnailMixin):
    TYPE = 'video_note'

    def __init__(self):
        super().__init__(self.TYPE)

    def parse_tg(self, event):
        super().parse_tg(event)
        self.duration = event.get('duration')

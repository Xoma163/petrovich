from apps.bot.core.chat_actions import ChatActionEnum
from apps.bot.core.messages.attachments.attachment import Attachment
from apps.bot.core.messages.attachments.mixins.duration_mixin import DurationMixin
from apps.bot.core.messages.attachments.mixins.sized_mixin import SizedMixin
from apps.bot.core.messages.attachments.mixins.thumbnail_mixin import ThumbnailMixin


class VideoAttachment(Attachment, ThumbnailMixin, SizedMixin, DurationMixin):
    TYPE = 'video'
    ACTIVITY = ChatActionEnum.UPLOAD_VIDEO

    def __init__(self):
        super().__init__(self.TYPE)
        self.m3u8_url = None

    def parse_tg(self, event):
        super().parse_tg(event)
        self.duration = event.get('duration')
        self.width = event.get('width')
        self.height = event.get('height')

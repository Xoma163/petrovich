from apps.bot.core.chat_actions import ChatActionEnum
from apps.bot.core.messages.attachments.attachment import Attachment
from apps.bot.core.messages.attachments.mixins.duration_mixin import DurationMixin
from apps.bot.core.messages.attachments.mixins.thumbnail_mixin import ThumbnailMixin


class AudioAttachment(Attachment, ThumbnailMixin, DurationMixin):
    TYPE = "audio"
    ACTION = ChatActionEnum.UPLOAD_AUDIO

    def __init__(self):
        super().__init__(self.TYPE)
        self.artist: str | None = None
        self.title: str | None = None

    def parse_tg(self, event):
        super().parse_tg(event)

        self.duration = event.get('duration')
        if event['mime_type'] == 'audio/mpeg':
            self.ext = 'mp3'

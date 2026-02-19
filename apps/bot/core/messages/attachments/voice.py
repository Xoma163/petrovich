from apps.bot.core.chat_actions import ChatActionEnum
from apps.bot.core.messages.attachments.attachment import Attachment
from apps.bot.core.messages.attachments.mixins.duration_mixin import DurationMixin


class VoiceAttachment(Attachment, DurationMixin):
    TYPE = "voice"
    ACTIVITY = ChatActionEnum.UPLOAD_AUDIO

    def __init__(self):
        super().__init__(self.TYPE)
        self.ext: str = 'ogg'

    def parse_tg(self, event):
        super().parse_tg(event)
        self.duration = event['duration']

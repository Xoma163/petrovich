from apps.bot.core.activities import ActivitiesEnum
from apps.bot.core.messages.attachments.attachment import Attachment
from apps.bot.core.messages.attachments.mixins.duration_mixin import DurationMixin


class VoiceAttachment(Attachment, DurationMixin):
    TYPE = "voice"
    ACTIVITY = ActivitiesEnum.UPLOAD_AUDIO

    def __init__(self):
        super().__init__(self.TYPE)
        self.ext: str = 'ogg'

    def parse_tg(self, event):
        self.duration = event['duration']
        self.size = event['file_size']
        self.file_id = event['file_id']

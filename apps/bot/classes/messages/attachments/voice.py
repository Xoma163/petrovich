from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.messages.attachments.attachment import Attachment
from apps.bot.classes.messages.attachments.mixins.duration_mixin import DurationMixin


class VoiceAttachment(Attachment, DurationMixin):
    TYPE = "voice"

    def __init__(self):
        super().__init__(self.TYPE)
        self.activity = ActivitiesEnum.UPLOAD_AUDIO
        self.ext: str = 'ogg'

    def parse_tg(self, event):
        self.duration = event['duration']
        self.size = event['file_size']
        self.file_id = event['file_id']

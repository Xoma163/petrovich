from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.messages.attachments.attachment import Attachment


class VoiceAttachment(Attachment):
    TYPE = "voice"

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration: float | None = None  # sec
        self.activity = ActivitiesEnum.UPLOAD_AUDIO
        self.ext = 'ogg'

    def parse_tg(self, event):
        self.duration = event['duration']
        self.size = event['file_size']
        self.file_id = event['file_id']

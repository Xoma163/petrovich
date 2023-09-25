from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.messages.attachments.attachment import Attachment


class VoiceAttachment(Attachment):
    TYPE = "voice"

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration = None  # sec
        self.activity = ActivitiesEnum.UPLOAD_AUDIO

    def parse_tg(self, event):
        self.duration = event['duration']
        self.size = event['file_size']
        self.file_id = event['file_id']

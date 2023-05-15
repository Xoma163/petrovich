from apps.bot.classes.messages.attachments.Attachment import Attachment


class VoiceAttachment(Attachment):
    TYPE = "voice"

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration = None  # sec

    def parse_tg(self, event):
        self.duration = event['duration']
        self.size = event['file_size']
        self.file_id = event['file_id']

from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.messages.attachments.attachment import Attachment


class AudioAttachment(Attachment):
    TYPE = "audio"

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration: float | None = None
        self.thumb = None

        self.artist = None
        self.title = None

        self.activity = ActivitiesEnum.UPLOAD_AUDIO
        self.ext: str | None = None

    def parse_tg(self, event):
        self.duration = event.get('duration')
        self.size = event['file_size']

        self.file_id = event['file_id']

        try:
            self.ext = event['file_name'].rsplit('.')[-1]
        except:
            if event['mime_type'] == 'audio/mpeg':
                self.ext = 'mp3'

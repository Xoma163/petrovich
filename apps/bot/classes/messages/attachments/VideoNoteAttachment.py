from apps.bot.classes.messages.attachments.Attachment import Attachment


class VideoNoteAttachment(Attachment):
    TYPE = 'video_note'

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration = None  # sec
        self.thumb: str = None

    def parse_tg(self, event, tg_bot):
        self.duration = event.get('duration')
        self.name = event.get('name')
        self.size = event['file_size']

        self.file_id = event['file_id']
        self.set_private_download_url_tg(tg_bot, self.file_id)

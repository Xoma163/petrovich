from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.messages.attachments.Attachment import Attachment


class GifAttachment(Attachment):
    TYPE = 'gif'

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration = None  # sec
        self.activity = ActivitiesEnum.UPLOAD_VIDEO

    def parse_tg(self, event):
        self.duration = event.get('duration')
        self.size = event['file_size']

        self.file_id = event['file_id']

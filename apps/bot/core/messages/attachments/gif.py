from apps.bot.core.activities import ActivitiesEnum
from apps.bot.core.messages.attachments.attachment import Attachment
from apps.bot.core.messages.attachments.mixins.duration_mixin import DurationMixin


class GifAttachment(Attachment, DurationMixin):
    TYPE = 'animation'
    ACTIVITY = ActivitiesEnum.UPLOAD_VIDEO

    def __init__(self):
        super().__init__(self.TYPE)

    def parse_tg(self, event):
        self.duration = event.get('duration')
        self.size = event['file_size']

        self.file_id = event['file_id']

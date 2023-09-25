from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.messages.attachments.attachment import Attachment


class DocumentAttachment(Attachment):
    TYPE = 'document'

    def __init__(self):
        super().__init__(self.TYPE)
        self.activity = ActivitiesEnum.UPLOAD_DOCUMENT

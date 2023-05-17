from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.messages.attachments.Attachment import Attachment


class DocumentAttachment(Attachment):
    TYPE = 'document'

    def __init__(self):
        super().__init__(self.TYPE)
        self.activity = ActivitiesEnum.UPLOAD_DOCUMENT

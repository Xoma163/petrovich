from apps.bot.classes2.messages.attachments.Attachment import Attachment


class DocumentAttachment(Attachment):

    def __init__(self):
        super().__init__('document')

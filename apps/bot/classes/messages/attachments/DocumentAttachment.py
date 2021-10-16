from apps.bot.classes.messages.attachments.Attachment import Attachment


class DocumentAttachment(Attachment):

    def __init__(self):
        super().__init__('document')

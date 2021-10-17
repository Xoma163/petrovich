from apps.bot.classes.messages.attachments.Attachment import Attachment


class LinkAttachment(Attachment):

    def __init__(self):
        super().__init__('link')

from apps.bot.classes.messages.attachments.Attachment import Attachment


class LinkAttachment(Attachment):
    TYPE = "link"
    def __init__(self):
        super().__init__(self.TYPE)

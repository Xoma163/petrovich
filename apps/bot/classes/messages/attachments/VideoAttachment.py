from apps.bot.classes.messages.attachments.Attachment import Attachment


class VideoAttachment(Attachment):

    def __init__(self):
        super().__init__()
        self.duration = None  # sec
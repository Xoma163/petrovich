from apps.bot.classes2.messages.attachments.Attachment import Attachment


class VideoAttachment(Attachment):

    def __init__(self):
        super().__init__('video')
        self.duration = None  # sec

from apps.bot.classes.messages.attachments.Attachment import Attachment


class GifAttachment(Attachment):
    TYPE = 'gif'

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration = None  # sec

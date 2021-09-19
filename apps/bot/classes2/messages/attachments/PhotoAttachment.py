from apps.bot.classes2.messages.attachments.Attachment import Attachment


class PhotoAttachment(Attachment):
    def __init__(self):
        super().__init__('photo')
        self.width = None
        self.height = None

    def get_max_photo_size(self):
        pass

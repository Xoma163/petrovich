from apps.bot.classes2.messages.attachments.Attachment import Attachment


class VoiceAttachment(Attachment):

    def __init__(self):
        super().__init__('voice')
        self.duration = None  # sec

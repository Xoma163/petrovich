from apps.bot.classes.messages.attachments.attachment import Attachment


class StickerAttachment(Attachment):
    TYPE = 'sticker'

    def __init__(self):
        super().__init__(self.TYPE)
        self.width: int | None = None
        self.height: int | None = None
        self.emoji: str | None = None
        self.animated: bool = False

    def parse_tg(self, event):
        attrs = ['width', 'height', 'file_id', 'file_size', 'emoji']
        for attr in attrs:
            setattr(self, attr, event.get(attr, None))
        self.animated = event['is_video'] or event['is_animated']

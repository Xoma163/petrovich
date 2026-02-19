from apps.bot.core.messages.attachments.attachment import Attachment
from apps.bot.core.messages.attachments.mixins.sized_mixin import SizedMixin


class StickerAttachment(Attachment, SizedMixin):
    TYPE = 'sticker'

    def __init__(self):
        super().__init__(self.TYPE)
        self.emoji: str | None = None
        self.animated: bool = False

    def parse_tg(self, event):
        super().parse_tg(event)

        self.width = event.get('width')
        self.height = event.get('height')
        self.emoji = event.get('emoji')
        self.animated = event['is_video'] or event['is_animated']

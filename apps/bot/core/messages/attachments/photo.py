from apps.bot.core.chat_actions import ChatActionEnum
from apps.bot.core.messages.attachments.attachment import Attachment
from apps.bot.core.messages.attachments.mixins.sized_mixin import SizedMixin


class PhotoAttachment(Attachment, SizedMixin):
    TYPE = "photo"
    ACTION = ChatActionEnum.UPLOAD_PHOTO

    def __init__(self):
        super().__init__(self.TYPE)


    def parse_tg(self, event):
        super().parse_tg(event)

        self.width = event.get('width')
        self.height = event.get('height')

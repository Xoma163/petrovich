from apps.bot.core.chat_actions import ChatActionEnum
from apps.bot.core.messages.attachments.attachment import Attachment
from apps.bot.core.messages.attachments.mixins.duration_mixin import DurationMixin


class GifAttachment(Attachment, DurationMixin):
    TYPE = 'animation'
    ACTION = ChatActionEnum.UPLOAD_VIDEO

    def __init__(self):
        super().__init__(self.TYPE)

    def parse_tg(self, event):
        super().parse_tg(event)
        self.duration = event.get('duration')

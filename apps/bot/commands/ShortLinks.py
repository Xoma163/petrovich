from apps.bot.APIs.BitLyAPI import BitLyAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem
from apps.bot.classes.messages.attachments.LinkAttachment import LinkAttachment


class ShortLinks(Command):
    name = "сс"
    names = ['cc']
    help_text = "сокращение ссылки"
    help_texts = [
        "(ссылка) - сокращение ссылки",
        "(Пересылаемое сообщение) - сокращение ссылки"
    ]
    attachments = [LinkAttachment]

    def start(self) -> ResponseMessage:
        if self.event.fwd:
            long_link = self.event.fwd[0].attachments[0].url
        else:
            long_link = self.event.attachments[0].url
        try:
            bl_api = BitLyAPI()
            answer = bl_api.get_short_link(long_link)
            return ResponseMessage(ResponseMessageItem(text=answer))
        except Exception:
            raise PWarning("Неверный формат ссылки")

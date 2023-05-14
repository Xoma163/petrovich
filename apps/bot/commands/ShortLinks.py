from apps.bot.APIs.BitLyAPI import BitLyAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Exceptions import PWarning
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

    def start(self):
        if self.event.fwd:
            long_link = self.event.fwd[0].attachments[0].url
        else:
            long_link = self.event.attachments[0].url
        try:
            bl_api = BitLyAPI()
            return bl_api.get_short_link(long_link)
        except Exception:
            raise PWarning("Неверный формат ссылки")

from apps.bot.APIs.BitLyAPI import BitLyAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Exceptions import PWarning


class ShortLinks(Command):
    name = "сс"
    names = ['cc']
    help_text = "сокращение ссылки"
    help_texts = [
        "(ссылка) - сокращение ссылки",
        "(Пересылаемое сообщение) - сокращение ссылки"
    ]
    args = 1

    def start(self):
        msgs = self.event.fwd
        if msgs:
            long_link = self.event.fwd[0]['text']
        else:
            long_link = self.event.message.args[0]
        try:
            bl_api = BitLyAPI()
            return bl_api.get_short_link(long_link)
        except Exception:
            raise PWarning("Неверный формат ссылки")

from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.classes.Command import Command


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
            short_link = self.bot.get_short_link(long_link)
        except Exception:
            raise PWarning("Неверный формат ссылки")
        return short_link

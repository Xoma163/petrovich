from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand


class ShortLinks(CommonCommand):
    names = ["сс", "cc"]
    help_text = "Сс - сокращение ссылки"
    detail_help_text = "Сс (ссылка) - сокращение ссылки\n" \
                       "Сс (Пересылаемое сообщение) - сокращение ссылки"
    args = 1

    def start(self):
        msgs = self.event.fwd
        if msgs:
            long_link = self.event.fwd[0]['text']
        else:
            long_link = self.event.args[0]
        try:
            short_link = self.bot.get_short_link(long_link)
        except Exception:
            raise PWarning("Неверный формат ссылки")
        return short_link

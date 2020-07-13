from apps.bot.classes.common.CommonCommand import CommonCommand


class ShortLinks(CommonCommand):
    def __init__(self):
        names = ["сс", "cc"]
        help_text = "Сс - сокращение ссылки"
        detail_help_text = "Сс (ссылка) - сокращение ссылки\n" \
                           "Сс (Пересылаемое сообщение) - сокращение ссылки"
        super().__init__(names, help_text, detail_help_text, args=1, platforms=['vk', 'api'], enabled=False)

    def start(self):
        msgs = self.event.fwd
        if msgs:
            long_link = self.event.fwd[0]['text']
        else:
            long_link = self.event.args[0]
        try:
            short_link = self.bot.get_short_link(long_link)
        except:
            return "Неверный формат ссылки"
        return short_link

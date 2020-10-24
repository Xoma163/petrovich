from apps.bot.classes.events.Event import Event


class TgEvent(Event):
    # По причине того, что вложения в телеге отправляются немного по ебаненькому,
    # они вынесены в TgBot: _setup_event_attachments
    def parse_attachments(self, attachments):
        return attachments

    def __init__(self, event):
        super().__init__(event)

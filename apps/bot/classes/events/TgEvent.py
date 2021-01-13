from apps.bot.classes.events.Event import Event


class TgEvent(Event):

    def parse_attachments(self, attachments):
        """
        Распаршивание вложений
        По причине того, что вложения в телеге отправляются немного по ебаненькому,
        они вынесены в TgBot: _setup_event_attachments
        """
        return attachments

    def __init__(self, event):
        super().__init__(event)

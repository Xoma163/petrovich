from apps.bot.classes_old.events.Event import Event, auto_str


@auto_str
class YandexEvent(Event):
    def parse_attachments(self, attachments):
        """
        Распаршивание вложений
        """
        return attachments

    def __init__(self, event):
        super().__init__(event)

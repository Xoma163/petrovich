from apps.bot.classes.events.Event import Event


class TgEvent(Event):
    def parse_attachments(self, tg_attachments):
        attachments = []
        if tg_attachments:
            for attachment in tg_attachments:
                new_attachment = {
                    'type': attachment['type']
                }

    def __init__(self, event):
        super().__init__(event)

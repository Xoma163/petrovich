from apps.bot.classes.events.Event import Event


class TgEvent(Event):
    def parse_attachments(self, vk_attachments):
        pass

    def __init__(self, event):
        super().__init__(event)

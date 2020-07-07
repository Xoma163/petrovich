from apps.bot.classes.events.Event import Event, auto_str


@auto_str
class VkEvent(Event):
    def parse_attachments(self, vk_attachments):
        pass

    def __init__(self, event):
        super().__init__(event)

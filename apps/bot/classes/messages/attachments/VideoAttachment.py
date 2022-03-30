from apps.bot.classes.messages.attachments.Attachment import Attachment


class VideoAttachment(Attachment):
    TYPE = 'video'
    def __init__(self):
        super().__init__(self.TYPE)
        self.duration = None  # sec

    def parse_vk_video(self, event_video):
        from petrovich.settings import VK_URL
        self.url = f"{VK_URL}video{event_video['owner_id']}_{event_video['id']}"
        self.duration = event_video['duration']

from apps.bot.classes.messages.attachments.Attachment import Attachment


class AudioAttachment(Attachment):
    TYPE = "audio"

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration = None
        self.thumb = None

        self.artist = None
        self.title = None

    def parse_vk(self, event):
        from petrovich.settings import VK_URL
        self.url = f"{VK_URL}video{event['owner_id']}_{event['id']}"
        self.private_download_url = event['url']
        self.duration = event['duration']

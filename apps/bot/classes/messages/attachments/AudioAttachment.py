from apps.bot.classes.messages.attachments.Attachment import Attachment


class AudioAttachment(Attachment):
    TYPE = "audio"

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration = None
        self.thumb = None

        self.artist = None
        self.title = None

    def parse_vk_audio(self, event_audio):
        from petrovich.settings import VK_URL
        self.url = f"{VK_URL}video{event_audio['owner_id']}_{event_audio['id']}"
        self.private_download_url = event_audio['url']
        self.duration = event_audio['duration']

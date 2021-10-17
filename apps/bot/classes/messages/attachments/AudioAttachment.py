from apps.bot.classes.messages.attachments.Attachment import Attachment


class AudioAttachment(Attachment):

    def __init__(self):
        super().__init__()
        self.duration = None

    def parse_vk_audio(self, event_audio):
        from petrovich.settings import VK_URL
        self.url = f"{VK_URL}video{event_audio['owner_id']}_{event_audio['id']}"
        self.private_download_url = event_audio['url']
        self.duration = event_audio['duration']

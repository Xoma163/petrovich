from apps.bot.classes.messages.attachments.Attachment import Attachment


class VideoAttachment(Attachment):
    TYPE = 'video'

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration = None  # sec
        self.width = None
        self.height = None

    def parse_vk_video(self, event_video):
        from petrovich.settings import VK_URL
        self.url = f"{VK_URL}video{event_video['owner_id']}_{event_video['id']}"
        self.duration = event_video['duration']

    def parse_tg_video(self, event_video, tg_bot):
        self.duration = event_video.get('duration')
        self.width = event_video.get('width')
        self.height = event_video.get('height')
        self.name = event_video.get('name')
        self.size = event_video['file_size']

        self.file_id = event_video['file_id']
        self.set_private_download_url_tg(tg_bot, self.file_id)

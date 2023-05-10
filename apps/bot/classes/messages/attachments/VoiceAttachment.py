from apps.bot.classes.messages.attachments.Attachment import Attachment


class VoiceAttachment(Attachment):
    TYPE = "voice"

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration = None  # sec

    def parse_tg(self, event, tg_bot):
        self.duration = event['duration']
        self.size = event['file_size']
        self.file_id = event['file_id']
        self.set_private_download_url_tg(tg_bot, self.file_id)

    def parse_vk(self, event):
        self.public_download_url = event['link_mp3']
        self.duration = event['duration']

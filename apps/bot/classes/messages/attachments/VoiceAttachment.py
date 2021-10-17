from apps.bot.classes.messages.attachments.Attachment import Attachment


class VoiceAttachment(Attachment):

    def __init__(self):
        super().__init__('voice')
        self.duration = None  # sec

    def parse_tg_voice(self, event_voice, tg_bot):
        self.duration = event_voice['duration']
        self.size = event_voice['file_size']
        file_id = event_voice['file_id']
        self.set_private_download_url_tg(tg_bot, file_id)

    def parse_vk_voice(self, event_voice):
        self.public_download_url = event_voice['link_mp3']
        self.duration = event_voice['duration']

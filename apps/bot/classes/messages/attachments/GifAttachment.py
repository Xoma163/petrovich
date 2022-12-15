from apps.bot.classes.messages.attachments.Attachment import Attachment


class GifAttachment(Attachment):
    TYPE = 'gif'

    def __init__(self):
        super().__init__(self.TYPE)
        self.duration = None  # sec

    def parse_tg_gif(self, event_gif, tg_bot):
        self.duration = event_gif.get('duration')
        self.width = event_gif.get('width')
        self.height = event_gif.get('height')
        self.size = event_gif['file_size']

        self.file_id = event_gif['file_id']
        self.set_private_download_url_tg(tg_bot, self.file_id)

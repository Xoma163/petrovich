from apps.bot.core.activities import ActivitiesEnum
from apps.bot.core.chat_activity import ChatActivity
from apps.commands.media_command.service import MediaServiceResponse, MediaService
from apps.connectors.parsers.media.sunoai import SunoAI


class SunoAIService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = SunoAI()

    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_AUDIO, self.event.peer_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url: str) -> MediaServiceResponse:
        data = self.service.get_info(url)

        title = f"{data.artists} - {data.title}"
        audio_att = self.bot.get_audio_attachment(
            data.download_url,
            peer_id=self.event.peer_id,
            filename=f"{title}.{data.format}",
            thumbnail_url=data.thumbnail_url,
            artist=data.artists,
            title=data.title
        )
        audio_att.download_content()
        audio_att.public_download_url = None

        return MediaServiceResponse(text=data.text, attachments=[audio_att])

    @classmethod
    def urls(cls) -> list[str]:
        return ['suno.ai', 'suno.com']

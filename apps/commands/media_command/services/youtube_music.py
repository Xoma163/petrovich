from apps.bot.core.activities import ActivitiesEnum
from apps.bot.core.chat_activity import ChatActivity
from apps.bot.utils.decorators import retry
from apps.commands.media_command.service import MediaServiceResponse, MediaService
from apps.connectors.parsers.media.youtube.music import YoutubeMusic
from apps.shared.exceptions import PWarning


class YoutubeMusicService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = YoutubeMusic()

    @retry(3, Exception, sleep_time=2, except_exceptions=(PWarning,))
    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_AUDIO, self.event.peer_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url: str) -> MediaServiceResponse:
        data = self.service.get_info(url)
        title = f"{data.artists} - {data.title}" if data.artists else data.title
        audio_att = self.bot.get_audio_attachment(
            data.content,
            peer_id=self.event.peer_id,
            filename=f"{title}.{data.format}",
            thumbnail_url=data.thumbnail_url,
            artist=data.artists,
            title=data.title
        )
        return MediaServiceResponse(text=None, attachments=[audio_att], video_title=data.title)

    @classmethod
    def urls(cls) -> list[str]:
        return ["music.youtube.com"]

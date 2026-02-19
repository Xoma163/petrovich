from apps.bot.core.chat_action_sender import ChatActionSender
from apps.bot.core.chat_actions import ChatActionEnum
from apps.commands.media_command.service import MediaServiceResponse, MediaService
from apps.connectors.parsers.media_command.youtube.music import YoutubeMusic
from apps.shared.decorators import retry
from apps.shared.exceptions import PWarning


class YoutubeMusicService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = YoutubeMusic()

    @retry(3, Exception, sleep_time=2, except_exceptions=(PWarning,))
    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActionSender(self.bot, ChatActionEnum.UPLOAD_AUDIO, self.event.peer_id, self.event.message_thread_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url: str) -> MediaServiceResponse:
        data = self.service.get_info(url)
        title = f"{data.artists} - {data.title}" if data.artists else data.title
        audio_att = self.bot.get_audio_attachment(
            _bytes=data.content,
            filename=f"{title}.{data.format}",
            peer_id=self.event.peer_id,
            thumbnail_url=data.thumbnail_url,
            artist=data.artists,
            title=data.title
        )
        return MediaServiceResponse(text=None, attachments=[audio_att], video_title=data.title)

    @classmethod
    def urls(cls) -> list[str]:
        return ["music.youtube.com"]

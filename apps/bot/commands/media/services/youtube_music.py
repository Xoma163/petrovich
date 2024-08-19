from apps.bot.api.media.youtube.music import YoutubeMusic
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.commands.media.service import MediaServiceResponse, MediaService
from apps.bot.utils.utils import retry


class YoutubeMusicService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.use_proxy = True
        self.service = YoutubeMusic(use_proxy=self.use_proxy)

    @retry(3, Exception, sleep_time=2)
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

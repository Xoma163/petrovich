from apps.bot.api.media.data import VideoData
from apps.bot.api.media.youtube.video import YoutubeVideo
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.exceptions import PSkipContinue, PWarning
from apps.bot.commands.media.service import MediaService, MediaServiceResponse
from apps.bot.utils.decorators import retry


class YoutubeVideoService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.use_proxy = False
        self.service = YoutubeVideo(use_proxy=self.use_proxy)

    @retry(3, Exception, sleep_time=2, except_exceptions=(PWarning,))
    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        video_data = self.service.get_video_info(url, high_res=self.media_keys.high_resolution)

        # Если нет форс флага, сообщение из чата, длительность видео более 2х минут, не было упоминания петровича, видео - не шортс тогда скип
        if not self.media_keys.force and self.event.is_from_chat and video_data.duration > 120 and not self.event.message.mentioned and not video_data.is_short_video:
            raise PSkipContinue()

        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_VIDEO, self.event.peer_id):
            return self._get_content_by_url(video_data, url)

    def _get_content_by_url(self, data: VideoData, url: str) -> MediaServiceResponse:

        if cached := self._get_cached(data.channel_id, data.video_id, data.title):
            return cached

        va = self.service.download_video(data)

        if self.media_keys.force_cache or va.get_size_mb() > self.bot.MAX_VIDEO_SIZE_MB:
            return self._cache_video(data.channel_id, data.video_id, data.title, url, va.content)

        return MediaServiceResponse(text=data.title, attachments=[va], video_title=data.title)

    def check_valid_url(self, url: str) -> None:
        self.service.check_url_is_video(url)

    @classmethod
    def urls(cls) -> list[str]:
        return ['www.youtube.com', 'youtube.com', "www.youtu.be", "youtu.be", "m.youtube.com"]

from apps.bot.core.chat_action_sender import ChatActionSender
from apps.bot.core.chat_actions import ChatActionEnum
from apps.commands.media_command.service import MediaService, MediaServiceResponse
from apps.connectors.parsers.media_command.data import VideoData
from apps.connectors.parsers.media_command.youtube.video import YoutubeVideo
from apps.shared.decorators import retry
from apps.shared.exceptions import PSkipContinue, PWarning


class YoutubeVideoService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = YoutubeVideo()

    @retry(3, Exception, sleep_time=2, except_exceptions=(PWarning,))
    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        video_data = self.service.get_video_info(url, high_res=self.media_keys.high_resolution)

        # Если нет форс флага, сообщение из чата, длительность видео более 2-х минут, не было упоминания петровича, видео - не шортс тогда скип
        if not self.media_keys.force and self.event.is_from_chat and video_data.duration > 120 and not self.event.message.mentioned and not video_data.is_short_video:
            raise PSkipContinue()

        with ChatActionSender(self.bot, ChatActionEnum.UPLOAD_VIDEO, self.event.peer_id):
            return self._get_content_by_url(video_data, url)

    def _get_content_by_url(self, data: VideoData, url: str) -> MediaServiceResponse:

        if cached := self._get_cached(data.channel_id, data.video_id, data.title):
            return cached

        va = self.service.download_video(data)

        if self.media_keys.force_cache or va.get_size_mb() > self.bot.max_video_size_mb:
            return self._cache_video(data.channel_id, data.video_id, data.title, url, va.content)

        return MediaServiceResponse(text=data.title, attachments=[va], video_title=data.title)

    def check_valid_url(self, url: str) -> None:
        self.service.check_url_is_video(url)

    @classmethod
    def urls(cls) -> list[str]:
        return ['www.youtube.com', 'youtube.com', "www.youtu.be", "youtu.be", "m.youtube.com"]

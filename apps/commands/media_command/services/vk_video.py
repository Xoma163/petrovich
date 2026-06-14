from apps.bot.core.chat_action_sender import ChatActionSender
from apps.bot.core.chat_actions import ChatActionEnum
from apps.commands.media_command.service import MediaService, MediaServiceResponse
from apps.connectors.parsers.media_command.vk_video import VKVideo
from apps.shared.decorators import retry
from apps.shared.exceptions import PWarning


class VKVideoService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = VKVideo(log_filter=self.event.log_filter)

    @retry(3, Exception, sleep_time=2, except_exceptions=(PWarning,))
    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActionSender(self.bot, ChatActionEnum.UPLOAD_VIDEO, self.event.peer_id, self.event.message_thread_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url: str) -> MediaServiceResponse:
        url = self.service.clear_url(url)

        data = self.service.get_video_info(url, high_res=self.media_keys.high_resolution)

        if not data:
            raise PWarning("Не получилось распарсить ссылку")

        if cached := self._get_cached(data.channel_id, data.video_id, data.title):
            return cached

        va = self.service.download_video(url, data=data, high_res=self.media_keys.high_resolution)

        if self._should_cache_attachment(va):
            return self._cache_video(data.channel_id, data.video_id, data.title, url, va.content)
        return MediaServiceResponse(text=data.title, attachments=[va], video_title=data.title)

    def check_valid_url(self, url: str) -> None:
        self.service.check_url_is_video(url)

    @classmethod
    def urls(cls) -> list[str]:
        return ["vk.com", "vkvideo.ru", "vk.ru"]

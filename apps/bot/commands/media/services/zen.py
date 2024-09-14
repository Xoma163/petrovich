from urllib.parse import urlparse

from apps.bot.api.media.zen import Zen
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.exceptions import PSkip
from apps.bot.commands.media.service import MediaServiceResponse, MediaService
from apps.bot.utils.utils import retry


class ZenService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = Zen()

    @retry(3, Exception, sleep_time=2)
    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_VIDEO, self.event.peer_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url: str) -> MediaServiceResponse:
        data = self.service.parse_video(url)

        if cached := self._get_cached(data.channel_id, data.video_id, data.title):
            return cached

        va = self.service.download_video(data)
        va.thumbnail_url = data.thumbnail_url
        va.width = data.width
        va.height = data.height
        if va.get_size_mb() > self.bot.MAX_VIDEO_SIZE_MB:
            return self._cache_video(data.channel_id, data.video_id, data.title, url, va.content)

        return MediaServiceResponse(text=data.title, attachments=[va], video_title=data.title)

    def check_valid_url(self, url: str) -> None:
        if urlparse(url).path.strip('/')[0] == "@":
            raise PSkip()

    @classmethod
    def urls(cls) -> list[str]:
        return ["dzen.ru"]

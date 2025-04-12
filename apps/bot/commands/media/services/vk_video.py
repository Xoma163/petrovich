import re

from apps.bot.api.media.vk.video import VKVideo
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.commands.media.service import MediaService, MediaServiceResponse
from apps.bot.utils.utils import retry


class VKVideoService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = VKVideo()

    @retry(3, Exception, sleep_time=2)
    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_VIDEO, self.event.peer_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url: str) -> MediaServiceResponse:
        r = re.findall(r'\?(list=.*)', url)
        if r:
            url = url.replace(r[0], "")
            url = url.rstrip("?")

        data = self.service.get_video_info(url)

        if not data:
            raise PWarning("Не получилось распарсить ссылку")

        if cached := self._get_cached(data.channel_id, data.video_id, data.title):
            return cached

        va = self.service.download(
            url,
            author_id=data.channel_id,
            video_id=data.video_id,
            high_res=self.media_keys.high_resolution
        )
        va.width = data.width
        va.height = data.height

        if self.media_keys.force_cache or va.get_size_mb() > self.bot.MAX_VIDEO_SIZE_MB:
            return self._cache_video(data.channel_id, data.video_id, data.title, url, va.content)
        return MediaServiceResponse(text=data.title, attachments=[va], video_title=data.title)

    @classmethod
    def urls(cls) -> list[str]:
        return ['vk.com', 'vkvideo.ru']

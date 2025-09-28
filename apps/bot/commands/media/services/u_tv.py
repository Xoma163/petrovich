from apps.bot.api.media.u_tv import UTV
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.commands.media.service import MediaService, MediaServiceResponse
from apps.bot.utils.decorators import retry


class UTVService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.use_proxy = True
        self.service = UTV()

    @retry(3, Exception, sleep_time=2, except_exceptions=(PWarning,))
    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_VIDEO, self.event.peer_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url) -> MediaServiceResponse:
        data = self.service.get_video_info(url)
        text = f"{data.channel_title} - {data.title}"

        if cached := self._get_cached(data.channel_id, data.video_id, text):
            return cached

        va = self.service.download(data)
        va.width = data.width
        va.height = data.height

        if self.media_keys.force_cache or va.get_size_mb() > self.bot.MAX_VIDEO_SIZE_MB:
            return self._cache_video(data.channel_id, data.video_id, text, url, va.content)
        return MediaServiceResponse(text=text, attachments=[va], video_title=text)

    @classmethod
    def urls(cls) -> list[str]:
        return ['u-tv.ru', 'www.u-tv.ru']

from apps.bot.api.media.boosty import Boosty
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.message import Message
from apps.bot.commands.media.service import MediaService, MediaServiceResponse
from apps.bot.utils.utils import retry


class BoostyService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = Boosty()

    @retry(3, AttributeError, sleep_time=2)
    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_VIDEO, self.event.peer_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url: str) -> MediaServiceResponse:
        auth_cookie = None
        if self.event.message.args and "token" in self.event.message.args[0]:
            auth_cookie = self.event.message.args_case[0]
            new_message = self.event.message.raw.replace(auth_cookie + "\n", '').replace(auth_cookie, '')
            self.event.message = Message(new_message)

        video_data = self.service.get_video_info(url, auth_cookie)

        if not video_data:
            raise PWarning("Не получилось распарсить ссылку")

        if cached := self._get_cached(video_data.channel_id, video_data.video_id, video_data.title):
            return cached

        va = self.service.download(video_data, high_res=self.media_keys.high_resolution)
        va.width = video_data.width
        va.height = video_data.height
        va.thumbnail_url = video_data.thumbnail_url

        if self.media_keys.force_cache or va.get_size_mb() > self.bot.MAX_VIDEO_SIZE_MB:
            return self._cache_video(video_data.channel_id, video_data.video_id, video_data.title, url, va.content)
        return MediaServiceResponse(text=video_data.title, attachments=[va], video_title=video_data.title)

    @classmethod
    def urls(cls) -> list[str]:
        return ['boosty.to']

from urllib.parse import urlparse

from apps.bot.api.media.tiktok import TikTok
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.exceptions import PSkipContinue, PWarning, PError
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.commands.media.service import MediaServiceResponse, MediaService
from apps.bot.utils.utils import retry


class TikTokService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = TikTok(log_filter=self.event.log_filter)

    @retry(3, Exception, except_exceptions=(PWarning, PError), sleep_time=2)
    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_VIDEO, self.event.peer_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url: str) -> MediaServiceResponse:
        ttd = self.service.get_video(url)
        va = VideoAttachment()
        va.public_download_url = ttd.video_url
        va.thumbnail_url = ttd.thumbnail_url
        return MediaServiceResponse(text=None, attachments=[va], video_title="")

    def check_valid_url(self, url: str) -> None:
        path = urlparse(url).path
        if "video/" in path:
            return

        if urlparse(url).path.strip('/')[0] == "@":
            raise PSkipContinue()

    @classmethod
    def urls(cls) -> list[str]:
        return ["www.tiktok.com", 'vm.tiktok.com', 'm.tiktok.com', 'vt.tiktok.com']

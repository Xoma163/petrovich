from urllib.parse import urlparse

from apps.bot.api.media.data import VideoData
from apps.bot.api.media.tiktok import TikTok
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.exceptions import PSkipContinue
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.commands.media.service import MediaServiceResponse, MediaService


class TikTokService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = TikTok()

    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_VIDEO, self.event.peer_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url: str) -> MediaServiceResponse:
        video_data: VideoData = self.service.get_video(url)
        va = VideoAttachment()
        va.public_download_url = video_data.video_download_url
        va.thumbnail_url = video_data.thumbnail_url
        va.width = video_data.width
        va.height = video_data.height
        va.download_content(
            cookies=video_data.extra_data['cookies'],
            headers=video_data.extra_data['headers']
        )

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

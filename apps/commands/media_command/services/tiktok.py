from urllib.parse import urlparse

from apps.bot.core.chat_action_sender import ChatActionSender
from apps.bot.core.chat_actions import ChatActionEnum
from apps.commands.media_command.service import MediaServiceResponse, MediaService
from apps.connectors.parsers.media_command.data import VideoData
from apps.connectors.parsers.media_command.tiktok import TikTok
from apps.shared.exceptions import PSkipContinue


class TikTokService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = TikTok()

    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActionSender(self.bot, ChatActionEnum.UPLOAD_VIDEO, self.event.peer_id, self.event.message_thread_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url: str) -> MediaServiceResponse:
        video_data: VideoData = self.service.get_video(url)
        va = self.bot.get_video_attachment(
            url=video_data.video_download_url,
            peer_id=self.event.peer_id,
            message_thread_id=self.event.message_thread_id,
            thumbnail_url=video_data.thumbnail_url,
            width=video_data.width,
            height=video_data.height,
        )
        va.download_content(
            cookies=video_data.extra_data['cookies'],  # noqa
            headers=video_data.extra_data['headers']  # noqa
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

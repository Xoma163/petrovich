from twitchdl import twitch
from twitchdl.commands.download import get_clip_authenticated_url

from apps.bot.core.chat_action_sender import ChatActionSender
from apps.bot.core.chat_actions import ChatActionEnum
from apps.commands.media_command.service import MediaServiceResponse, MediaService


class TwitchClipsService(MediaService):

    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActionSender(self.bot, ChatActionEnum.UPLOAD_VIDEO, self.event.peer_id, self.event.message_thread_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url: str) -> MediaServiceResponse:
        slug = url.split(self.urls()[0], 1)[-1].lstrip('/')
        clip_info = twitch.get_clip(slug)
        title = clip_info['title']
        video_url = get_clip_authenticated_url(slug, "source")
        video = self.bot.get_video_attachment(
            url=video_url,
            peer_id=self.event.peer_id,
            message_thread_id=self.event.message_thread_id,
        )
        video.download_content()
        return MediaServiceResponse(text=title, attachments=[video], video_title=title)

    @classmethod
    def urls(cls) -> list[str]:
        return ['clips.twitch.tv']

from twitchdl import twitch
from twitchdl.commands.download import get_clip_authenticated_url

from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.commands.media.service import MediaServiceResponse, MediaService


class TwitchClipsService(MediaService):

    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_VIDEO, self.event.peer_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url: str) -> MediaServiceResponse:
        slug = url.split(self.urls[0], 1)[-1].lstrip('/')
        clip_info = twitch.get_clip(slug)
        title = clip_info['title']
        video_url = get_clip_authenticated_url(slug, "source")
        video = self.bot.get_video_attachment(video_url, peer_id=self.event.peer_id)
        video.download_content()
        return MediaServiceResponse(text=title, attachments=[video], video_title=title)

    @classmethod
    def urls(cls) -> list[str]:
        return ['clips.twitch.tv']

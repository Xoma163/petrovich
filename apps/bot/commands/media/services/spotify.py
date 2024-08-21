import re

from apps.bot.api.media.spotify import Spotify
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.commands.media.service import MediaServiceResponse, MediaService


class SpotifyService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = Spotify()

    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_AUDIO, self.event.peer_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url: str) -> MediaServiceResponse:
        tracks = re.findall(r'track\/(\w*)', url)
        track_id = tracks[0]

        data = self.service.get_info(track_id)

        title = f"{data.artists} - {data.title}"
        audio_att = self.bot.get_audio_attachment(
            data.content,
            peer_id=self.event.peer_id,
            filename=f"{title}.{data.format}",
            thumbnail_url=data.thumbnail_url,
            artist=data.artists,
            title=data.title
        )
        return MediaServiceResponse(text=None, attachments=[audio_att])

    def check_valid_url(self, url: str) -> None:
        tracks = re.findall(r'track\/(\w*)', url)
        if not tracks:
            raise PWarning("Я могу обрабатывать только ссылки на треки")

    @classmethod
    def urls(cls) -> list[str]:
        return ['open.spotify.com']

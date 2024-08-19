from apps.bot.api.media.yandex.music import YandexMusicAPI, YandexAlbum, YandexTrack
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.commands.media.service import MediaServiceResponse, MediaService


class YandexMusicService(MediaService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = YandexMusicAPI()

    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_AUDIO, self.event.peer_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url: str) -> MediaServiceResponse:
        res = self.service.parse_album_and_track_ids(url)
        if res['album_id'] and not res['track_id']:
            ya = YandexAlbum(res['album_id'])
            ya.set_tracks()
            tracks = ya.tracks
        else:
            yt = YandexTrack(res['track_id'])
            tracks = [yt]

        audios = []
        for track in tracks:
            audiofile = track.download()
            title = f"{track.artists} - {track.title}"
            audio = self.bot.get_audio_attachment(
                audiofile,
                peer_id=self.event.peer_id,
                filename=f"{title}.{track.format}",
                thumbnail_url=track.thumbnail_url,
                artist=track.artists,
                title=track.title
            )
            audios.append(audio)
        return MediaServiceResponse(text=None, attachments=audios)

    @classmethod
    def urls(cls) -> list[str]:
        return ["music.yandex.ru"]

    def check_sender_role(self) -> None:
        if not self.event.sender.check_role(Role.TRUSTED):
            raise PWarning("Медиа яндекс музыка доступен только для доверенных пользователей")

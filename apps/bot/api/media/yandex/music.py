import logging
import re
from urllib.parse import urlparse

from yandex_music import Client, Track
from yandex_music.utils.request import Request

from apps.bot.classes.const.exceptions import PWarning
from petrovich.settings import env

logging.basicConfig(level=logging.CRITICAL)


class YandexMusicAPI:
    # https://github.com/MarshalX/yandex-music-api/discussions/513#discussioncomment-2729781
    ACCESS_TOKEN = env.str("YANDEX_MUSIC_ACCESS_TOKEN")

    def __init__(self):
        self._client: Client | None = None

    def get_client(self):
        if not self._client:
            Client._Client__notice_displayed = True
            self._client = Client(request=YandexRequest(), token=self.ACCESS_TOKEN)
            self._client.init()
        return self._client

    @staticmethod
    def parse_album_and_track_ids(url: str):
        parsed_url = urlparse(url)
        url = f"{parsed_url.scheme}://{parsed_url.hostname}{parsed_url.path}"

        album_id, track_id = None, None

        r = re.compile(r"https://(?:next.)?music.yandex.(?:ru|com)/album/(\d*)/track/(\d*)")
        try:
            album_id, track_id = r.findall(url)[0]
        except IndexError:
            try:
                r = re.compile(r"https://(?:next.)?music.yandex.(?:ru|com)/track/(\d*)")
                track_id = r.findall(url)[0]
            except IndexError:
                try:
                    r = re.compile(r"https://(?:next.)?music.yandex.(?:ru|com)/album/(\d*)")
                    album_id = r.findall(url)[0]
                except IndexError:
                    raise PWarning("Не нашёл песни по этому URL")

        return {
            "album_id": album_id,
            "track_id": track_id
        }


class YandexTrack(YandexMusicAPI):
    def __init__(self, _id: str = None, track: Track = None):
        super().__init__()

        if _id is None and track is None:
            raise RuntimeError("id or track must be provided")

        self.track: Track | None = None

        if track:
            self.track: Track = track
        elif _id:
            client = self.get_client()
            self.track: Track = client.tracks(_id)[0]

        self.albums: str = ""
        self.artists: str = ""
        self.title: str = ""
        self.thumbnail_url: str = ""

        self.bitrate: int = 0
        self.format: str = ""

    def download(self) -> bytes:
        self.albums = ", ".join([album.title for album in self.track.albums])
        self.title = self.track.title
        self.artists = ", ".join([artist.name for artist in self.track.artists])
        if self.track.cover_uri:
            self.thumbnail_url = f'https://{self.track.cover_uri.replace("%%", "300x300")}'
        info = self.track.get_download_info()[0]
        self.bitrate = info.bitrate_in_kbps
        self.format = info.codec
        if not info.direct_link:
            info.get_direct_link()
        mp3 = info.client.request.download(info.direct_link, None)
        return mp3


class YandexAlbum(YandexMusicAPI):
    def __init__(self, _id: str):
        super().__init__()

        self.id: str = _id
        self.tracks: list[YandexTrack] = []

    def set_tracks(self):
        client = self.get_client()
        tracks: list[Track] = client.albums_with_tracks(self.id).volumes[0]
        self.tracks = [YandexTrack(track=x) for x in tracks]


# service redefinition
class YandexRequest(Request):
    def download(self, url, timeout=5, *args, **kwargs) -> bytes:
        return self.retrieve(url, timeout=timeout, *args, *kwargs)

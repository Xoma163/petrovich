import logging
import re
from urllib.parse import urlparse

from apps.bot.classes.consts.Exceptions import PWarning
from petrovich.settings import env

logging.basicConfig(level=logging.CRITICAL)
from yandex_music import Client
from yandex_music.utils.request import Request


class YandexMusicAPI:
    # https://github.com/MarshalX/yandex-music-api/discussions/513#discussioncomment-2729781
    ACCESS_TOKEN = env.str("YANDEX_MUSIC_ACCESS_TOKEN")

    def __init__(self, url):
        parsed_url = urlparse(url)
        self.url = f"{parsed_url.scheme}://{parsed_url.hostname}{parsed_url.path}"
        r = re.compile(r"https://music.yandex.ru/album/(.*)/track/(.*)")
        try:
            self.album_id, self.track_id = r.findall(self.url)[-1]
        except IndexError:
            try:
                r = re.compile(r"https://music.yandex.ru/track/(.*)")
                self.track_id = r.findall(self.url)[-1]
            except:
                raise PWarning("Не нашёл песни по этому URL")
        self.albums = ""
        self.artists = ""
        self.title = ""
        self.cover_url = ""

        self.bitrate = 0
        self.format = ""

    def download_track(self):
        client = YandeClient(request=YandexRequest(), token=self.ACCESS_TOKEN)
        client.notice_displayed = True
        client.init()

        track = client.tracks(self.track_id)[0]
        self.albums = ", ".join([album.title for album in track.albums])
        self.title = track.title
        self.artists = ", ".join([artist.name for artist in track.artists])
        self.cover_url = f'https://{track.cover_uri.replace("%%", "400x400")}'
        info = track.get_download_info()[0]
        self.bitrate = info.bitrate_in_kbps
        self.format = info.codec
        if not info.direct_link:
            info.get_direct_link()
        mp3 = info.client.request.download(info.direct_link, None)
        return mp3


# service redefinition
class YandexRequest(Request):
    def download(self, url, timeout=5, *args, **kwargs) -> bytes:
        return self.retrieve(url, timeout=timeout, *args, *kwargs)


# service redefinition
class YandeClient(Client):
    def __init__(self, token: str = None, base_url: str = None, request: Request = None, language: str = 'ru',
                 report_unknown_fields=False):
        self.logger = logging.getLogger('yandex_music.client')
        self.token = token

        if base_url is None:
            base_url = 'https://api.music.yandex.net'

        self.base_url = base_url

        self.report_unknown_fields = report_unknown_fields

        if request:
            self._request = request
            self._request.set_and_return_client(self)
        else:
            self._request = Request(self)

        self.language = language
        self._request.set_language(self.language)

        self.device = (
            'os=Python; os_version=; manufacturer=Marshal; '
            'model=Yandex Music API; clid=; device_id=random; uuid=random'
        )

        self.me = None

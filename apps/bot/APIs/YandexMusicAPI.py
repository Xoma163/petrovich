import urllib

from yandex_music import Client
from yandex_music.utils.request import Request


class YandexRequest(Request):
    def download(self, url, timeout=5, *args, **kwargs) -> bytes:
        return self.retrieve(url, timeout=timeout, *args, *kwargs)


class YandexMusicAPI:
    def __init__(self, url):
        self.url = url
        self.id = urllib.parse.urlparse(url).path.split('/')[-1]
        self.albums = ""
        self.artists = ""
        self.title = ""

        self.bitrate = 0
        self.format = ""

    def download_track(self):
        client = Client(request=YandexRequest())
        client.init()

        track = client.tracks(self.id)[0]
        self.albums = ", ".join([album.title for album in track.albums])
        self.title = track.title
        self.artists = ", ".join([artist.name for artist in track.artists])
        info = track.get_download_info()[0]
        self.bitrate = info.bitrate_in_kbps
        self.format = info.codec
        if not info.direct_link:
            info.get_direct_link()
        mp3 = info.client.request.download(info.direct_link, None)
        return mp3

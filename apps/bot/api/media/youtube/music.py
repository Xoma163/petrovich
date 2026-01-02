import os
from urllib.parse import urlparse, parse_qsl

import yt_dlp

from apps.bot.api.media.data import AudioData
from apps.bot.utils.nothing_logger import NothingLogger
from apps.bot.utils.proxy import get_proxies


class YoutubeMusic:
    def __init__(self, use_proxy=True):
        self._temp_file_path = ""

        self.proxies = None
        self.use_proxy = use_proxy
        if self.use_proxy:
            self.proxies = get_proxies()

    @staticmethod
    def clear_url(url):
        parsed = urlparse(url)
        v = dict(parse_qsl(parsed.query)).get('v')
        res = f"{parsed.scheme}://{parsed.hostname}{parsed.path}"
        if v:
            res += f"?v={v}"
        return res

    def get_info(self, url) -> AudioData:
        try:
            return self._get_info(url)
        finally:
            self.delete_temp_file()

    def _get_info(self, url) -> AudioData:
        ydl_params = {
            'format': 'bestaudio/best',
            'title': True,
            'logger': NothingLogger(),
            # 'outtmpl': '/tmp/yt_dlp_%(title)s-%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
        }
        if self.use_proxy:
            ydl_params['proxy'] = self.proxies['https']

        ytdl = yt_dlp.YoutubeDL(ydl_params)
        url = self.clear_url(url)

        info = ytdl.extract_info(url, download=True)
        self._temp_file_path = info['requested_downloads'][0]['filepath']
        artist = info.get('artist')
        if artist:
            artist = artist.split(',')[0]
        title = info.get('title')
        full_title = info.get('fulltitle')

        if not artist or not title:
            artists = artist
        else:
            full_title = full_title.replace('—', '-').replace('–', '-').replace('−', '-')
            try:
                artists, title = full_title.split('-')
            except ValueError:
                artists = info['uploader']
                title = full_title

            artists = artists.strip()
            title = title.strip()

        with open(self._temp_file_path, 'rb') as file:
            content = file.read()

        return AudioData(
            artists=artists,
            title=title,
            duration=info.get('duration'),
            thumbnail_url=self._get_thumbnail(info),
            format=info['requested_downloads'][0]['ext'],
            content=content,
        )

    @staticmethod
    def _get_thumbnail(info: dict) -> str | None:
        try:
            return list(filter(
                lambda x: x['url'].endswith("mqdefault.jpg"),
                info['thumbnails']
            ))[0]['url']
        except (IndexError, KeyError):
            return None

    def delete_temp_file(self):
        os.remove(self._temp_file_path)

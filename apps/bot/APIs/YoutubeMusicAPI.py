import os
from urllib.parse import urlparse, parse_qsl

import yt_dlp

from apps.bot.utils.NothingLogger import NothingLogger


class YoutubeMusicAPI:
    def __init__(self, url):
        self.url = url

        self.duration = 0

        self.albums = ""
        self.artists = ""
        self.title = ""
        self.cover_url = ""

        self.bitrate = 0
        self.format = ""

        self.content = None
        self._temp_file_path = ""

    @property
    def clear_url(self):
        parsed = urlparse(self.url)
        v = dict(parse_qsl(parsed.query)).get('v')
        res = f"{parsed.scheme}://{parsed.hostname}{parsed.path}"
        if v:
            res += f"?v={v}"
        return res

    def get_info(self):
        try:
            self._get_info()
        finally:
            self.delete_temp_file()

    def _get_info(self):
        ytdl = yt_dlp.YoutubeDL({
            'format': 'bestaudio/best',
            'title': True,
            'logger': NothingLogger(),
            'outtmpl': '/tmp/yt_dlp_%(title)s-%(id)s.%(ext)s'
        })
        info = ytdl.extract_info(self.clear_url, download=True)
        self._temp_file_path = info['requested_downloads'][0]['_filename']
        artist = info.get('artist')
        if artist:
            artist = artist.split(',')[0]
        title = info.get('title')
        full_title = info.get('fulltitle')

        if artist and title:
            self.title = title
            self.artists = artist
        else:
            full_title = full_title.replace('—', '-').replace('–', '-').replace('−', '-')
            try:
                self.artists, self.title = full_title.split('-')
            except ValueError:
                self.artists = info['uploader']
                self.title = full_title

            self.artists = self.artists.strip()
            self.title = self.title.strip()

        self.duration = info.get('duration')
        self.cover_url = f"https://i.ytimg.com/vi/{info['id']}/mqdefault.jpg"
        self.format = info.get('ext')
        with open(self._temp_file_path, 'rb') as file:
            self.content = file.read()

    def delete_temp_file(self):
        os.remove(self._temp_file_path)

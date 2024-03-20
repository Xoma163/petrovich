import os
from urllib.parse import urlparse, parse_qsl

import yt_dlp

from apps.bot.utils.nothing_logger import NothingLogger


class YoutubeMusic:
    def __init__(self):
        self._temp_file_path = ""

    @staticmethod
    def clear_url(url):
        parsed = urlparse(url)
        v = dict(parse_qsl(parsed.query)).get('v')
        res = f"{parsed.scheme}://{parsed.hostname}{parsed.path}"
        if v:
            res += f"?v={v}"
        return res

    def get_info(self, url):
        try:
            return self._get_info(url)
        finally:
            self.delete_temp_file()

    def _get_info(self, url) -> dict:
        ytdl = yt_dlp.YoutubeDL({
            'format': 'bestaudio/best',
            'title': True,
            'logger': NothingLogger(),
            'outtmpl': '/tmp/yt_dlp_%(title)s-%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],

        })
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
        return {
            "artists": artists,
            "title": title,
            "duration": info.get('duration'),
            "cover_url": f"https://i.ytimg.com/vi/{info['id']}/mqdefault.jpg",
            "format": info['requested_downloads'][0]['ext'],
            "content": content
        }

    def delete_temp_file(self):
        os.remove(self._temp_file_path)

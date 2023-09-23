import re

import requests

from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.VideoDownloader import VideoDownloader


class PremiereAPI:
    def __init__(self, url: str):
        self.url = url

        self.title = ""
        self.show_name = ""
        self.season = ""
        self.episode = ""

        self.video_id = None

    def parse_video(self):
        res = re.findall(r"show/(.*)/season/(.*)/episode/(.*)", self.url)
        if not res:
            raise PWarning("Не смог распарсить это видео")
        self.show_name, self.season, self.episode = res[0]

        params = {"season": self.season, 'episode': self.episode}
        r = requests.get(f"https://premier.one/uma-api/metainfo/tv/{self.show_name}/video/", params=params).json()
        result = r['results'][0]
        self.video_id = result['id']
        self.title = result['title_for_player']

    def download_video(self):
        if not self.video_id:
            self.parse_video()

        r = requests.get(
            f"https://premier.one/api/play/options/{self.video_id}/?format=json&no_404=true&referer={self.url}").json()
        master_m3u8_url = r['video_balancer']['default']

        vd = VideoDownloader()
        return vd.download(master_m3u8_url, threads=10)

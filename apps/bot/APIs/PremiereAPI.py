import re

import requests

from apps.bot.utils.VideoDownloader import VideoDownloader


class PremiereAPI:
    def __init__(self, url: str):
        if url and not url.endswith("/"):
            url += "/"
        self.url = url

        self.title = ""
        self.show_id = ""
        self.show_name = ""
        self.season = ""
        self.episode = ""

        self.video_id = None

        self.is_series = False
        self.is_movie = False

    def parse_video(self):
        res = re.findall(r"show/(.*)/season/(.*)/episode/(.*)/", self.url)
        res2 = re.findall(r"show/(.*)/", self.url)
        if res:
            self.show_id, self.season, self.episode = res[0]
            self._parse_series()
        elif res2:
            self.show_id = res2[0]
            self._parse_movie()

    def parse_show(self):
        res2 = re.findall(r"show/(.*)/", self.url)
        self.show_id = res2[0]
        params = {'limit': 100}
        r = requests.get(f"https://premier.one/uma-api/metainfo/tv/{self.show_id}/video/", params=params).json()
        results = r['results']
        videos = [x for x in results if x.get('type', {}).get('id') == 6]
        trailers = [x for x in results if x.get('type', {}).get('id') == 5]

        return {
            'show_id': res2[0],
            'title': trailers[0].get('title') if trailers else self.show_id,
            'last_video_id': videos[-2]['id']
        }

    @staticmethod
    def get_last_video_ids_with_titles(show_id, last_video_id):
        params = {'limit': 100}
        r = requests.get(f"https://premier.one/uma-api/metainfo/tv/{show_id}/video/", params=params).json()
        results = r['results']

        videos = [x for x in results if x.get('type', {}).get('id') == 6]

        ids = [x['id'] for x in videos]
        titles = [x['title'] for x in videos]
        urls = [f"https://premier.one/show/{show_id}/season/{x['season']}/episode/{x['episode']}" for x in videos]

        try:
            index = ids.index(last_video_id) + 1
            ids = ids[index:]
            titles = titles[index:]
            urls = urls[index:]
        except IndexError:
            pass

        return ids, titles, urls

    def _parse_series(self):
        self.is_series = True

        params = {"season": self.season, 'episode': self.episode}
        r = requests.get(f"https://premier.one/uma-api/metainfo/tv/{self.show_id}/video/", params=params).json()
        result = r['results'][0]
        self.video_id = result['id']
        self.title = result['title_for_player'] or result['title_for_card']

    def _parse_movie(self):
        self.is_movie = True
        r = requests.get(f"https://premier.one/uma-api/metainfo/tv/{self.show_id}/video/").json()
        result = r['results'][0]
        self.video_id = result['id']
        self.title = result['title_for_player'] or result['title_for_card']

    def download_video(self):
        if not self.video_id:
            self.parse_video()

        r = requests.get(
            f"https://premier.one/api/play/options/{self.video_id}/?format=json&no_404=true&referer={self.url}").json()
        master_m3u8_url = r['video_balancer']['default']

        vd = VideoDownloader()
        return vd.download(master_m3u8_url, threads=10)

import logging
import re
from typing import List

import requests

from apps.bot.api.subscribe_service import SubscribeService
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.video.downloader import VideoDownloader

logger = logging.getLogger('responses')


class Premier(SubscribeService):
    def parse_video(self, url: str) -> dict:
        url = self._prepare_url(url)

        res = re.findall(r"show/(.*)/season/(.*)/episode/(.*)/", url)
        res2 = re.findall(r"show/(.*)/", url)
        if res:
            show_id, season, episode = res[0]
            data = self._parse_series(show_id, season, episode)
            data.update({
                "show_id": show_id,
                "season": season,
                "episode": episode,
                "is_series": True,
                "filename": f"{show_id}_s{season}e{episode}"
            })
        elif res2:
            show_id = res2[0]
            data = self._parse_movie(show_id)
            data.update({
                "show_id": show_id,
                "is_series": False,
                "filename": data['show_id'],
            })
        else:
            raise PWarning("Не распознал ссылку как фильм или сериал")
        return data

    def _parse_series(self, show_id: str, season: str, episode: str) -> dict:
        params = {"season": season, 'episode': episode}
        result = self._get_videos(show_id, params)[0]
        return {
            "video_id": result['id'],
            "title": result['title_for_player'] or result['title_for_card']
        }

    def _parse_movie(self, show_id: str) -> dict:
        result = self._get_videos(show_id, {})[0]
        return {
            "video_id": result['id'],
            "title": result['title_for_player'] or result['title_for_card']
        }

    @staticmethod
    def _get_download_url(video_id: str, url: str, log_results: bool = True):
        r = requests.get(
            f"https://premier.one/api/play/options/{video_id}/?format=json&no_404=true&referer={url}").json()
        if log_results:
            logger.debug({"response": r})
        if 'video_balancer' not in r:
            raise PWarning("Не могу скачать это видео. Либо оно платное, либо чёт ещё...")
        return r['video_balancer']['default']

    def download_video(self, video_id: str, url: str) -> bytes:
        master_m3u8_url = self._get_download_url(url, video_id)
        vd = VideoDownloader()
        return vd.download(master_m3u8_url, threads=10)

    @staticmethod
    def _get_videos(channel_id: str, params: dict, log_results: bool = True) -> dict:
        r = requests.get(f"https://premier.one/uma-api/metainfo/tv/{channel_id}/video/", params=params).json()
        if log_results:
            logger.debug({"response": r})
        results = r['results']
        return results

    @staticmethod
    def _prepare_url(url):
        if not url.endswith('/'):
            url += "/"
        return url

    def get_data_to_add_new_subscribe(self, url: str) -> dict:
        url = self._prepare_url(url)

        res2 = re.findall(r"show/(.*)/", url)
        show_id = res2[0]

        params = {'limit': 100}
        results = self._get_videos(show_id, params)

        videos = [x for x in results if x.get('type', {}).get('id') == 6 and x.get('season') > 0]
        trailers = [x for x in results if x.get('type', {}).get('id') == 5]

        if videos:
            return {
                'channel_id': show_id,
                'playlist_id': None,
                'channel_title': trailers[0].get('title') if trailers else show_id,
                'playlist_title': None,
                'last_videos_id': [x['id'] for x in videos],
            }

    def get_filtered_new_videos(self, channel_id: str, last_videos_id: List[str], **kwargs) -> dict:
        params = {'limit': 100}
        results = self._get_videos(channel_id, params, log_results=False)

        videos = [x for x in results if x.get('type', {}).get('id') == 6]

        ids = [x['id'] for x in videos]
        titles = [x['title'] for x in videos]
        urls = [f"https://premier.one/show/{channel_id}/season/{x['season']}/episode/{x['episode']}" for x in videos]

        index = self.filter_by_id(ids, last_videos_id)

        ids = ids[index:]
        titles = titles[index:]
        urls = urls[index:]

        data = {"ids": [], "titles": [], "urls": []}
        for i, url in enumerate(urls):
            try:
                self._get_download_url(ids[i], url, log_results=False)

                data['ids'].append(ids[i])
                data['titles'].append(titles[i])
                data['urls'].append(urls[i])
            except PWarning:
                continue
        return data

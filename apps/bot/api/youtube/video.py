from datetime import timedelta
from typing import List
from urllib import parse
from urllib.parse import urlparse, parse_qsl

import requests
import yt_dlp
from bs4 import BeautifulSoup

from apps.bot.api.subscribe_service import SubscribeService
from apps.bot.classes.const.exceptions import PWarning, PSkip
from apps.bot.utils.nothing_logger import NothingLogger
from petrovich.settings import env


class YoutubeVideo(SubscribeService):
    def __init__(self):
        super().__init__()

    @staticmethod
    def get_timecode_str(url) -> str:
        """
        Переводит таймкод из секунд в [часы:]минуты:секунды
        """
        t = dict(parse_qsl(urlparse(url).query)).get('t')
        if t:
            t = t.rstrip('s')
            h, m, s = str(timedelta(seconds=int(t))).split(":")
            if h:
                return f"{h}:{m}:{s}"
            return f"{m}:{s}"
        return ""

    @staticmethod
    def _clear_url(url) -> str:
        parsed = urlparse(url)
        v = dict(parse_qsl(parsed.query)).get('v')
        res = f"{parsed.scheme}://{parsed.hostname}{parsed.path}"
        if v:
            res += f"?v={v}"
        return res

    def _get_video_info(self, url) -> dict:
        ydl_params = {
            'logger': NothingLogger()
        }
        ydl = yt_dlp.YoutubeDL(ydl_params)
        ydl.add_default_info_extractors()

        url = self._clear_url(url)
        try:
            video_info = ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as e:
            if "Sign in to confirm your age" in e.msg:
                raise PWarning("К сожалению видос доступен только залогиненым пользователям")
            raise PWarning("Не смог найти видео по этой ссылке")
        return video_info

    def get_video_info(self, url, _timedelta=None, max_filesize_mb=None) -> dict:
        video_info = self._get_video_info(url)
        video_urls = [x for x in video_info['formats'] if x['ext'] == 'mp4' and x.get('asr')]
        if not video_urls:
            raise PWarning("Нет доступных ссылок для скачивания")

        videos = sorted(video_urls, key=lambda x: x['format_note'], reverse=True)
        chosen_video_filesize = 0
        if max_filesize_mb:  # for tg
            for video in videos:
                filesize = video.get('filesize') or video.get('filesize_approx')
                if filesize:
                    chosen_video_filesize = filesize / 1024 / 1024

                    if chosen_video_filesize < max_filesize_mb:
                        max_quality_video = video
                        break
                    if _timedelta:
                        mbps = chosen_video_filesize / video_info.get('duration')
                        if mbps * _timedelta < max_filesize_mb - 2:
                            max_quality_video = video
                            break
            else:
                raise PSkip()
        else:
            max_quality_video = videos[0]

        url = max_quality_video['url']
        return {
            "download_url": url,
            "filesize": chosen_video_filesize,
            "title": video_info['title'],
            "duration": video_info.get('duration'),
            "start_pos": str(video_info['section_start']) if video_info.get('section_start') else None,
            "end_pos": str(video_info['section_end']) if video_info.get('section_end') else None
        }

    @staticmethod
    def _get_channel_info(channel_id: str) -> dict:
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            "id": channel_id,
            "key": env.str('GOOGLE_API_KEY'),
            "part": "snippet"
        }
        r = requests.get(url, params=params).json()
        if not r['items']:
            raise PWarning("Не нашёл канал")
        return {
            "author": r['items'][0]['snippet']['title']
        }

    @staticmethod
    def _get_channel_videos(channel_id: str) -> list:

        r = requests.get(f"https://www.scriptbarrel.com/xml.cgi?channel_id={channel_id}")
        if r.status_code != 200:
            raise PWarning("Не нашёл такого канала")
        bsop = BeautifulSoup(r.content, 'lxml')
        videos = [x.find('yt:videoid').text for x in bsop.find_all('entry')]

        return list(reversed(videos))

    @staticmethod
    def _get_playlist_info(channel_id: str) -> dict:
        url = "https://www.googleapis.com/youtube/v3/playlists"
        params = {
            "id": channel_id,
            "key": env.str('GOOGLE_API_KEY'),
            "part": "snippet"
        }
        r = requests.get(url, params=params).json()
        if not r['items']:
            raise PWarning("Не нашёл плейлист")

        snippet = r['items'][0]['snippet']
        return {
            "title": snippet['title'],
            "author": snippet['channelTitle'],
            "channel_id": snippet['channelId']
        }

    @staticmethod
    def _get_playlist_videos(playlist_id: str) -> list:
        url = "https://www.googleapis.com/youtube/v3/playlistItems"
        params = {
            "playlistId": playlist_id,
            "part": "snippet",
            "maxResults": 50,
            "key": env.str('GOOGLE_API_KEY'),
        }
        videos = []
        while True:
            r = requests.get(url, params=params).json()
            videos += r['items']
            if not r.get('nextPageToken'):
                break
            params['pageToken'] = r['nextPageToken']
        videos = [x for x in videos if x['snippet']['resourceId'].get('videoId')]
        return videos

    def get_data_to_add_new_subscribe(self, url: str) -> dict:
        r = requests.get(url)
        bs4 = BeautifulSoup(r.content, 'lxml')
        href = bs4.find_all('link', {'rel': 'canonical'})[0].attrs['href']
        get_params = dict(parse.parse_qsl(parse.urlsplit(href).query))

        playlist_id = None
        playlist_title = None

        if get_params.get('list'):
            playlist_id = get_params.get('list')
            last_videos = self._get_playlist_videos(playlist_id)
            last_videos_id = [x['snippet']['resourceId']['videoId'] for x in last_videos]

            playlist_info = self._get_playlist_info(playlist_id)

            channel_id = playlist_info['channel_id']
            playlist_title = playlist_info['title']
            channel_title = playlist_info['author']
        else:
            channel_id = href.split('/')[-1]
            last_videos_id = self._get_channel_videos(channel_id)
            channel_title = self._get_channel_info(channel_id)['author']
        return {
            'channel_id': channel_id,
            'playlist_id': playlist_id,
            'channel_title': channel_title,
            'playlist_title': playlist_title,
            'last_videos_id': last_videos_id,
        }

    def get_filtered_new_videos(self, channel_id: str, last_videos_id: List[str], **kwargs) -> dict:
        if kwargs.get('playlist_id'):
            videos = self._get_playlist_videos(kwargs.get('playlist_id'))
            ids = [x['snippet']['resourceId']['videoId'] for x in videos]
        else:
            ids = self._get_channel_videos(channel_id)

        index = self.filter_by_id(ids, last_videos_id)

        ids = ids[index:]
        urls = [f"https://www.youtube.com/watch?v={x}" for x in ids]

        data = {"ids": [], "titles": [], "urls": []}
        for i, url in enumerate(urls):
            try:
                video_info = self._get_video_info(url)
            except PWarning:
                continue
            if video_info['duration'] <= 60:
                continue
            data['ids'].append(ids[i])
            data['titles'].append(video_info['title'])
            data['urls'].append(urls[i])
        return data

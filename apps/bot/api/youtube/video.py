from datetime import timedelta
from urllib.parse import urlparse, parse_qsl

import requests
import yt_dlp
from bs4 import BeautifulSoup

from apps.bot.api.subscribe_service import SubscribeService
from apps.bot.classes.const.exceptions import PWarning, PSkip
from apps.bot.utils.nothing_logger import NothingLogger


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
            "duration": video_info.get('duration')
        }

    def get_data_to_add_new_subscribe(self, url: str) -> dict:
        r = requests.get(url)
        bs4 = BeautifulSoup(r.content, 'lxml')
        channel_id = bs4.find_all('link', {'rel': 'canonical'})[0].attrs['href'].split('/')[-1]

        r = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
        if r.status_code != 200:
            raise PWarning("Не нашёл такого канала")
        bsop = BeautifulSoup(r.content, 'lxml')
        last_video = bsop.find_all('entry')[0]

        return {
            'channel_id': channel_id,
            'title': bsop.find('title').text,
            'last_video_id': last_video.find('yt:videoid').text,
            'playlist_id': None
        }

    def get_filtered_new_videos(self, channel_id: str, last_video_id: str, **kwargs) -> dict:
        r = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
        if r.status_code != 200:
            raise PWarning("Не нашёл такого канала")
        bsop = BeautifulSoup(r.content, 'lxml')

        videos = reversed(bsop.find_all('entry'))
        ids = [x.find("yt:videoid").text for x in videos]
        titles = [x.find("title").text for x in videos]

        index = ids.index(last_video_id) + 1

        ids = ids[index:]
        titles = titles[index:]
        urls = [f"https://www.youtube.com/watch?v={x}" for x in ids]

        data = {"ids": [], "titles": [], "urls": []}
        for i, url in enumerate(urls):
            video_info = self._get_video_info(url)
            if video_info['duration'] < 60:
                continue
            data['ids'].append(ids[i])
            data['titles'].append(titles[i])
            data['urls'].append(urls[i])
        return data

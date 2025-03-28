import re
from datetime import timedelta
from urllib import parse
from urllib.parse import urlparse, parse_qsl

import requests
import yt_dlp
from bs4 import BeautifulSoup
from requests.exceptions import SSLError

from apps.bot.api.media.data import VideoData
from apps.bot.api.subscribe_service import SubscribeService, SubscribeServiceNewVideosData, \
    SubscribeServiceNewVideoData, SubscribeServiceData
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.utils.nothing_logger import NothingLogger
from apps.bot.utils.proxy import get_proxies
from apps.bot.utils.utils import retry
from apps.bot.utils.video.downloader import VideoDownloader
from apps.bot.utils.video.video_handler import VideoHandler
from apps.service.models import SubscribeItem
from petrovich.settings import env


class YoutubeVideo(SubscribeService):
    DEFAULT_VIDEO_QUALITY_HIGHT = 1080

    def __init__(self, use_proxy=True):
        super().__init__()

        self.proxies = None
        self.use_proxy = use_proxy
        if self.use_proxy:
            self.proxies = get_proxies()

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
    def clear_url(url) -> str:
        parsed = urlparse(url)
        v = dict(parse_qsl(parsed.query)).get('v')
        res = f"{parsed.scheme}://{parsed.hostname}{parsed.path}"
        if v:
            res += f"?v={v}"
        return res

    def check_url_is_video(self, url):
        url = self.clear_url(url)
        r = r"((youtube.com\/watch\?v=)|(youtu.be\/)|(youtube.com\/shorts\/))"
        res = re.findall(r, url)
        if not res:
            raise PWarning("Ссылка должна быть на видео, не на канал")

    def _get_video_info(self, url: str) -> dict:
        ydl_params = {
            'logger': NothingLogger(),
        }
        if self.use_proxy:
            ydl_params['proxy'] = self.proxies['https']
        ydl = yt_dlp.YoutubeDL(ydl_params)
        ydl.add_default_info_extractors()

        try:
            video_info = ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as e:
            if "Sign in to confirm your age" in e.msg:
                raise PWarning("К сожалению видос доступен только залогиненым пользователям")
            raise PWarning("Не смог найти видео по этой ссылке")
        return video_info

    def get_video_info(
            self,
            url,
            high_res=False,
            _timedelta: float | None = None
    ) -> VideoData:
        video_info = self._get_video_info(url)

        video, audio, filesize = self._get_video_download_urls(video_info, high_res, _timedelta)

        return VideoData(
            filesize=filesize,
            video_download_url=video['url'] if video else None,
            # video_download_chunk_size=video['downloader_options']['http_chunk_size'] if video else None,
            audio_download_url=audio['url'],
            # audio_download_chunk_size=audio['downloader_options']['http_chunk_size'],
            title=video_info['title'],
            duration=video_info.get('duration'),
            width=video.get('width'),
            height=video.get('height'),
            start_pos=str(video_info['section_start']) if video_info.get('section_start') else None,
            end_pos=str(video_info['section_end']) if video_info.get('section_end') else None,
            thumbnail_url=self._get_thumbnail(video_info),
            channel_id=video_info['channel_id'],
            video_id=video_info['id'],
            channel_title=video_info['channel']
        )

    def download_video(self, data: VideoData) -> VideoAttachment:
        if not data.video_download_url or not data.audio_download_url:
            raise ValueError
        _va = VideoAttachment()
        _va.m3u8_url = data.video_download_url
        vd = VideoDownloader(_va)
        _va.content = vd.download_m3u8(threads=10, use_proxy=self.use_proxy)

        _aa = AudioAttachment()
        _aa.m3u8_url = data.audio_download_url
        vd = VideoDownloader(_aa)
        _aa.content = vd.download_m3u8(threads=2, use_proxy=self.use_proxy)

        vh = VideoHandler(video=_va, audio=_aa)
        content = vh.mux()

        va = VideoAttachment()
        va.content = content
        va.width = data.width or None
        va.height = data.height or None
        va.duration = data.duration or None
        va.thumbnail_url = data.thumbnail_url or None
        va.use_proxy_on_download_thumbnail = True
        return va

    @staticmethod
    def _get_thumbnail(info: dict) -> str | None:
        video_scale = info['width'] / info['height']

        # Вертикальное видео
        if video_scale < 1:
            thumbnails = list(filter(
                lambda x: x.get('width') and x.get('height') and x.get('width') / x.get('height') == video_scale,
                info['thumbnails']
            ))
        else:
            thumbnails = list(filter(
                lambda x: x['url'].endswith("maxresdefault.jpg"),
                info['thumbnails']
            ))

        if not thumbnails:
            return None

        try:
            return thumbnails[0]['url']
        except (IndexError, KeyError):
            return None

    def _get_video_download_urls(
            self,
            video_info: dict,
            high_res: bool = False,
            _timedelta: int | None = None,
    ) -> tuple[dict, dict, int]:
        """
        Метод ищет видео которое максимально может скачать с учётом ограничением платформы
        return: max_quality_video, max_quality_audio
        """
        video_formats = list(
            filter(
                lambda x: (
                        x.get('vbr') and  # Это видео
                        x.get('ext') == 'mp4' and  # С форматом mp4
                        x.get('vcodec') not in ['vp9'] and  # С кодеками которые поддерживают все платформы
                        x.get('dynamic_range') == 'SDR'  # В SDR качестве
                    # x.get('format_note')  # Имеют разрешение для просмотра (?)
                ),
                video_info['formats']
            )
        )
        for _format in video_formats:
            _format['filesize_approx_vbr'] = video_info['duration'] * _format.get('vbr')
        video_formats = sorted(
            video_formats,
            key=self._filesize_key,
            reverse=True
        )

        audio_formats = sorted(
            [x for x in video_info['formats'] if x.get('language')],  # abr
            key=self._filesize_key,
            reverse=True
        )

        try:
            ru_audio_formats = [x for x in audio_formats if x.get('language') == 'ru']
            af = ru_audio_formats[0]
        except IndexError:
            af = audio_formats[0]
        vf = video_formats[0]

        if not high_res:
            for vf in video_formats:
                if int(vf['height']) <= self.DEFAULT_VIDEO_QUALITY_HIGHT:
                    break

        video_filesize = (self._filesize_key(vf) + self._filesize_key(af)) / 1024 / 1024
        return vf, af, video_filesize

    @staticmethod
    def _filesize_key(x):
        return x.get('filesize', x.get('filesize_approx', x.get('filesize_approx_vbr', 0)))

    @retry(3, SSLError, sleep_time=2)
    def _get_channel_info(self, channel_id: str) -> dict:
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            "id": channel_id,
            "key": env.str('GOOGLE_API_KEY'),
            "part": "snippet"
        }
        r = requests.get(url, params=params, proxies=self.proxies).json()
        if not r['items']:
            raise PWarning("Не нашёл канал")
        return {
            "author": r['items'][0]['snippet']['title']
        }

    @retry(3, SSLError, sleep_time=2)
    def _get_channel_videos(self, channel_id: str) -> list:
        r = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}", proxies=self.proxies)
        if r.status_code != 200:
            raise PWarning("Не нашёл такого канала")
        bsop = BeautifulSoup(r.content, 'xml')
        videos = [x.find('yt:videoId').text for x in bsop.find_all('entry')]
        return list(reversed(videos))

    @retry(3, SSLError, sleep_time=2)
    def _get_playlist_info(self, channel_id: str) -> dict:
        url = "https://www.googleapis.com/youtube/v3/playlists"
        params = {
            "id": channel_id,
            "key": env.str('GOOGLE_API_KEY'),
            "part": "snippet"
        }
        r = requests.get(url, params=params, proxies=self.proxies).json()
        if not r['items']:
            raise PWarning("Не нашёл плейлист")

        snippet = r['items'][0]['snippet']
        return {
            "title": snippet['title'],
            "author": snippet['channelTitle'],
            "channel_id": snippet['channelId']
        }

    @retry(3, SSLError, sleep_time=2)
    def _get_playlist_videos(self, playlist_id: str) -> list:
        url = "https://www.googleapis.com/youtube/v3/playlistItems"
        params = {
            "playlistId": playlist_id,
            "part": "snippet",
            "maxResults": 50,
            "key": env.str('GOOGLE_API_KEY'),
        }
        videos = []
        while True:
            r = requests.get(url, params=params, proxies=self.proxies).json()

            if error := r.get('error'):
                if error['code'] == 404:
                    raise PWarning("Плейлист не найден")
                raise PWarning("Ошибка получения плейлиста API")
            videos += r['items']
            if not r.get('nextPageToken'):
                break
            params['pageToken'] = r['nextPageToken']
        videos = [x for x in videos if x['snippet']['resourceId'].get('videoId')]
        return videos

    @retry(3, SSLError, sleep_time=2)
    def get_channel_info(self, url: str) -> SubscribeServiceData:
        r = requests.get(url, proxies=self.proxies)
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
        return SubscribeServiceData(
            channel_id=channel_id,
            playlist_id=playlist_id,
            channel_title=channel_title,
            playlist_title=playlist_title,
            last_videos_id=last_videos_id,
            service=SubscribeItem.SERVICE_YOUTUBE

        )

    def get_filtered_new_videos(
            self,
            channel_id: str,
            last_videos_id: list[str],
            **kwargs
    ) -> SubscribeServiceNewVideosData:
        if kwargs.get('playlist_id'):
            videos = self._get_playlist_videos(kwargs.get('playlist_id'))
            ids = [x['snippet']['resourceId']['videoId'] for x in videos]
        else:
            ids = self._get_channel_videos(channel_id)

        index = self.filter_by_id(ids, last_videos_id)

        ids = ids[index:]
        urls = [f"https://www.youtube.com/watch?v={x}" for x in ids]

        data = SubscribeServiceNewVideosData(videos=[])
        for i, url in enumerate(urls):
            try:
                video_info = self._get_video_info(url)
            except PWarning:
                continue
            if video_info['duration'] <= 60:
                continue
            video = SubscribeServiceNewVideoData(
                id=ids[i],
                title=video_info['title'],
                url=url
            )
            data.videos.append(video)
        return data

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
from apps.bot.classes.const.exceptions import PWarning, PSubscribeIndexError
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.utils.decorators import retry
from apps.bot.utils.nothing_logger import NothingLogger
from apps.bot.utils.proxy import get_proxies
from apps.bot.utils.video.downloader import VideoDownloader
from apps.bot.utils.video.video_handler import VideoHandler
from apps.service.models import SubscribeItem
from petrovich.settings import env


class YoutubeVideo(SubscribeService):
    DEFAULT_VIDEO_QUALITY_HIGHT = 720
    DOMAIN = "youtube.com"
    URL = f"https://{DOMAIN}"

    def __init__(self, use_proxy=True):
        super().__init__()

        self.proxies = None
        self.use_proxy = use_proxy
        if self.use_proxy:
            self.proxies = get_proxies()

    # SERVICE METHODS

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
            audio_download_url=audio['url'],
            title=video_info['title'],
            duration=video_info.get('duration'),
            width=video.get('width'),
            height=video.get('height'),
            start_pos=str(video_info['section_start']) if video_info.get('section_start') else None,
            end_pos=str(video_info['section_end']) if video_info.get('section_end') else None,
            thumbnail_url=self._get_thumbnail(video_info),
            channel_id=video_info['channel_id'],
            video_id=video_info['id'],
            channel_title=video_info['channel'],
            is_short_video="/shorts/" in url or video_info.get('media_type') == 'short',
            extra_data={
                'http_chunk_size_video': video.get('downloader_options', {}).get('http_chunk_size', 10 * 1024 * 1024),
                'http_chunk_size_audio': audio.get('downloader_options', {}).get('http_chunk_size', 10 * 1024 * 1024),
            }
        )

    def download_video(self, data: VideoData) -> VideoAttachment:
        if not data.video_download_url or not data.audio_download_url:
            raise ValueError
        _va = VideoAttachment()
        _va.m3u8_url = data.video_download_url
        vd = VideoDownloader(_va)
        http_chunk_size_video = data.extra_data.get('http_chunk_size_video')
        _va.content = vd.download_m3u8(threads=16, use_proxy=self.use_proxy, http_chunk_size=http_chunk_size_video)

        _aa = AudioAttachment()
        _aa.m3u8_url = data.audio_download_url
        vd = VideoDownloader(_aa)
        http_chunk_size_audio = data.extra_data.get('http_chunk_size_audio')
        _aa.content = vd.download_m3u8(threads=8, use_proxy=self.use_proxy, http_chunk_size=http_chunk_size_audio)

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

    # -----------------------------

    # SUBSCRIBE METHODS

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
            last_videos_ids = last_videos['ids']

            playlist_info = self._get_playlist_info(playlist_id)
            channel_id = playlist_info['channel_id']
            playlist_title = playlist_info['title']
            channel_title = playlist_info['author']
        else:
            channel_id = href.split('/')[-1]
            last_videos = self._get_channel_videos(channel_id)
            last_videos_ids = last_videos['ids']

            channel_info = self._get_channel_info(channel_id)
            channel_title = channel_info['author']

        return SubscribeServiceData(
            channel_id=channel_id,
            playlist_id=playlist_id,
            channel_title=channel_title,
            playlist_title=playlist_title,
            last_videos_id=last_videos_ids,
            service=SubscribeItem.SERVICE_YOUTUBE
        )

    def get_filtered_new_videos(
            self,
            channel_id: str,
            last_videos_id: list[str],
            **kwargs
    ) -> SubscribeServiceNewVideosData:
        if kwargs.get('playlist_id'):
            videos = self._get_playlist_videos(kwargs['playlist_id'])
        else:
            videos = self._get_channel_videos(channel_id)
        ids = videos['ids']
        titles = videos['titles']
        urls = videos['urls']

        index = self.filter_by_id(ids, last_videos_id)
        if len(ids) == index:
            return SubscribeServiceNewVideosData(videos=[])

        ids = ids[index:]
        titles = titles[index:]
        urls = urls[index:]

        data = SubscribeServiceNewVideosData(videos=[])
        for i, _ in enumerate(ids):
            try:
                video_info = self.get_video_info(urls[i])
            except PWarning:
                raise PSubscribeIndexError([ids[i]])
            if video_info.is_short_video:
                continue
            video = SubscribeServiceNewVideoData(
                id=ids[i],
                title=titles[i],
                url=urls[i]
            )
            data.videos.append(video)
        return data

    # -----------------------------

    # UTILS

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

    def _get_video_url(self, video_id) -> str:
        return f"{self.URL}/watch?v={video_id}"

    def check_url_is_video(self, url):
        url = self.clear_url(url)
        r = rf"(({self.DOMAIN}\/watch\?v=)|(youtu.be\/)|({self.DOMAIN}\/shorts\/))"
        res = re.findall(r, url)
        if not res:
            raise PWarning("Ссылка должна быть на видео, не на канал")

    @staticmethod
    def _filesize_key(x):
        if filesize := x.get('filesize'):
            return filesize
        if filesize_approx := x.get('filesize_approx'):
            return filesize_approx
        if filesize_approx_vbr := x.get('filesize_approx_vbr'):
            return filesize_approx_vbr * 100
        return 0

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

    # -----------------------------

    # VIDEO DOWNLOAD HELPERS

    def _get_video_info(self, url: str) -> dict:
        ydl_params = {
            'logger': NothingLogger(),
            'noplaylist': True,
            # Не забыть закинуть deno в /usr/bin/local
            'js_runtimes': {'deno': {}},
            'remote_components': ['ejs:npm', 'ejs:github'],
            # 'cookiefile': os.path.join(BASE_DIR, 'secrets', 'youtube_cookies.txt')
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
            elif "Sign in to confirm you’re not a bot" in e.msg:
                raise PWarning("Ютуб думает что я бот (да я бот). Попробуйте скачать видео позже")
            elif "The following content is not available on this app" in e.msg:
                raise PWarning("Это видео скачать не получится. ПАТАМУШТА")
            elif "Requested format is not available." in e.msg:
                raise PWarning("Ютуб отвалился. Создайте ишу, чтобы разраб обновил библиотечку плиз c:")
            elif "This video has been removed for violating YouTube's Community Guidelines" in e.msg:
                raise PWarning("Это видео было удалено за нарушение правил YouTube")
            else:
                raise PWarning("Не смог найти видео по этой ссылке")
        return video_info

    def _get_video_download_urls(
            self,
            video_info: dict,
            high_res: bool = False,
            _timedelta: int | None = None,
    ) -> tuple[dict, dict, int]:
        """
        Метод ищет видео которое максимально может скачать с учётом ограничением платформы
        return: video_format, audio_format, video_filesize
        """
        audio_formats = sorted(
            [x for x in video_info['formats'] if x['resolution'] == 'audio only'],  # abr
            key=self._filesize_key,
            reverse=True
        )

        # Выбор аудио-формата по языковой дорожке
        for lang in ('ru', 'en-US'):
            af = next((x for x in audio_formats if x.get('language') == lang), None)
            if af:
                break
        if not af and audio_formats:
            af = audio_formats[0]

        video_formats = list(
            filter(
                lambda x: (
                        x.get('vbr') and  # Это видео
                        x.get('ext') == 'mp4' and  # С форматом mp4
                        x.get('vcodec') not in ['vp9'] and  # С кодеками которые поддерживают все платформы
                        x.get('dynamic_range') == 'SDR' and  # В SDR качестве
                        not x.get('__working')  # Без тестовых
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

        vf = video_formats[0]
        if not high_res:
            for vf in video_formats:
                if int(vf['height']) <= self.DEFAULT_VIDEO_QUALITY_HIGHT:
                    break

        video_filesize = (self._filesize_key(vf) + self._filesize_key(af)) / 1024 / 1024
        return vf, af, video_filesize

    # -----------------------------

    # CHANNEL/PLAYLISTS INFO GETTERS

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
    def _get_channel_videos(self, channel_id: str) -> dict:
        r = requests.get(f"{self.URL}/feeds/videos.xml?channel_id={channel_id}", proxies=self.proxies)
        if r.status_code != 200:
            raise PWarning("Не нашёл такого канала")
        bsop = BeautifulSoup(r.content, 'xml')
        ids = [x.find('yt:videoId').text for x in reversed(bsop.find_all('entry'))]
        return {
            "ids": ids,
            "titles": [x.find('title').text for x in reversed(bsop.find_all('entry'))],
            "urls": [self._get_video_url(_id) for _id in ids]
        }

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
    def _get_playlist_videos(self, playlist_id: str) -> dict:
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
        ids = [v['snippet']['resourceId']['videoId'] for v in videos]
        return {
            "ids": ids,
            "titles": [v['snippet']['title'] for v in videos],
            "urls": [self._get_video_url(_id) for _id in ids]
        }

    # -----------------------------

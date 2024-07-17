import dataclasses
import re
from datetime import timedelta
from urllib import parse
from urllib.parse import urlparse, parse_qsl

import requests
import yt_dlp
from bs4 import BeautifulSoup

from apps.bot.api.subscribe_service import SubscribeService, SubscribeServiceNewVideosData, SubscribeServiceNewVideoData
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.utils.nothing_logger import NothingLogger
from apps.bot.utils.video.video_handler import VideoHandler
from petrovich.settings import env


@dataclasses.dataclass
class YoutubeVideoData:
    video_download_url: str
    video_download_chunk_size: int | None
    audio_download_url: str
    audio_download_chunk_size: int | None
    filesize: int
    title: str
    duration: int | None
    width: int | None
    height: int | None
    start_pos: str
    end_pos: str
    thubmnail_url: str


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

    @staticmethod
    def check_url_is_video(url):
        r = r"((youtube.com\/watch\?v=)|(youtu.be\/)|(youtube.com\/shorts\/))"
        return re.findall(r, url)

    def _get_video_info(self, url) -> dict:
        ydl_params = {
            'logger': NothingLogger()
        }
        ydl = yt_dlp.YoutubeDL(ydl_params)
        ydl.add_default_info_extractors()

        url = self._clear_url(url)
        if not self.check_url_is_video(url):
            raise PWarning("Ссылка должна быть на видео, не на канал")
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
            max_filesize_mb: int | None = None,
            _timedelta: float | None = None
    ) -> YoutubeVideoData:
        video_info = self._get_video_info(url)

        video, audio, filesize = self._get_video_download_urls(video_info, max_filesize_mb, _timedelta)

        return YoutubeVideoData(
            filesize=filesize,
            video_download_url=video['url'] if video else None,
            video_download_chunk_size=video['downloader_options']['http_chunk_size'] if video else None,
            audio_download_url=audio['url'],
            audio_download_chunk_size=audio['downloader_options']['http_chunk_size'],
            title=video_info['title'],
            duration=video_info.get('duration'),
            width=video.get('width'),
            height=video.get('height'),
            start_pos=str(video_info['section_start']) if video_info.get('section_start') else None,
            end_pos=str(video_info['section_end']) if video_info.get('section_end') else None,
            thubmnail_url=self._get_thumbnail(video_info)
        )

    @staticmethod
    def download_video(data: YoutubeVideoData) -> VideoAttachment:
        if not data.video_download_url or not data.audio_download_url:
            raise ValueError

        _va = VideoAttachment()
        _va.public_download_url = data.video_download_url
        _va.download_content(chunk_size=data.video_download_chunk_size)
        _aa = AudioAttachment()
        _aa.public_download_url = data.audio_download_url
        _aa.download_content(chunk_size=data.audio_download_chunk_size)

        vh = VideoHandler(video=_va, audio=_aa)
        content = vh.mux()

        va = VideoAttachment()
        va.content = content
        va.width = data.width
        va.height = data.height
        va.duration = data.duration
        return va

    @staticmethod
    def _get_thumbnail(info: dict) -> str | None:
        try:
            return list(filter(
                lambda x: x['url'].endswith("mqdefault.jpg"),
                info['thumbnails']
            ))[0]['url']
        except (IndexError, KeyError):
            return None

    @staticmethod
    def _get_video_download_urls(
            video_info: dict,
            max_filesize_mb: int | None = None,
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
                ),
                video_info['formats']
            )
        )
        for _format in video_formats:
            _format['filesize_approx_vbr'] = video_info['duration'] * _format.get('vbr')
        video_formats = sorted(
            video_formats,
            key=lambda x: x.get('filesize') or x.get('filesize_approx') or x.get('filesize_approx_vbr'),
            reverse=True
        )

        audio_formats = sorted(
            [x for x in video_info['formats'] if x.get('acodec') == 'opus'],
            key=lambda x: x['filesize'],
            reverse=True
        )

        best_audio_format = audio_formats[0]
        best_video_format = video_formats[0] if max_filesize_mb is None else None

        for video_format in video_formats:
            if best_video_format:
                break
            video_filesize = (video_format['filesize'] + best_audio_format['filesize']) / 1024 / 1024
            if _timedelta:
                video_filesize = video_filesize * _timedelta / video_info.get('duration')
            if video_filesize < max_filesize_mb:
                best_video_format = video_format

        if not best_video_format:
            raise ValueError()

        video_filesize = (best_video_format['filesize'] + best_audio_format['filesize']) / 1024 / 1024
        return best_video_format, best_audio_format, video_filesize

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
        r = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
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

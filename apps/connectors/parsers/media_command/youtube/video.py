import re
from datetime import timedelta
from urllib.parse import urlparse, parse_qsl

import yt_dlp

from apps.bot.core.messages.attachments.audio import AudioAttachment
from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.connectors.parsers.media_command.data import VideoData
from apps.connectors.parsers.media_command.youtube.nothing_logger import NothingLogger
from apps.shared.exceptions import PWarning
from apps.shared.utils.video.downloader import VideoDownloader
from apps.shared.utils.video.video_handler import VideoHandler


class YoutubeVideo:
    DEFAULT_VIDEO_QUALITY_HIGHT = 720
    DOMAIN = "youtube.com"
    URL = f"https://{DOMAIN}"

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
        _va.content = vd.download_m3u8(threads=16, http_chunk_size=http_chunk_size_video)

        _aa = AudioAttachment()
        _aa.m3u8_url = data.audio_download_url
        vd = VideoDownloader(_aa)
        http_chunk_size_audio = data.extra_data.get('http_chunk_size_audio')
        _aa.content = vd.download_m3u8(threads=8, http_chunk_size=http_chunk_size_audio)

        vh = VideoHandler(video=_va, audio=_aa)
        content = vh.mux()

        va = VideoAttachment()
        va.content = content
        va.width = data.width or None
        va.height = data.height or None
        va.duration = data.duration or None
        va.thumbnail_url = data.thumbnail_url or None
        return va

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
        }
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

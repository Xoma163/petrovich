import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import yt_dlp

from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.connectors.parsers.media_command.data import VideoData
from apps.shared.exceptions import PWarning
from apps.shared.utils.video.yt_dlp_video_downloader import YtDlpVideoDownloader


class VKVideo:
    DEFAULT_VIDEO_QUALITY_HEIGHT = 1080
    VIDEO_URL_RE = re.compile(r"(?:^|/)(video|clip)-?\d+_\d+")
    CLIP_URL_RE = re.compile(r"(?:^|/)clip-?\d+_\d+")

    def __init__(self, log_filter: dict | None = None):
        super().__init__()
        self.log_filter = log_filter
        self.downloader = YtDlpVideoDownloader(ytdlp_error_handler=self._prepare_ytdlp_error)

    # SERVICE METHODS

    def get_video_info(self, url: str, high_res: bool = False) -> VideoData:
        info = self._get_video_info(url)
        video_format = self._get_video_format(info, high_res=high_res)
        format_id = video_format.get("format_id")
        if video_format.get("acodec") == "none":
            format_id = None

        return VideoData(
            channel_id=self._get_channel_id(info),
            video_id=info["id"],
            channel_title=info.get("uploader") or info.get("channel"),
            title=info.get("title") or "Видео VK",
            width=video_format.get("width") or info.get("width"),
            height=video_format.get("height") or info.get("height"),
            duration=info.get("duration"),
            thumbnail_url=info.get("thumbnail"),
            filesize_mb=self._filesize_key(video_format) / 1024 / 1024,
            extra_data={
                "format_id": format_id,
            },
        )

    def download_video(self, url: str, data: VideoData, high_res: bool = False) -> VideoAttachment:
        format_id = data.extra_data.get("format_id") if data.extra_data else None
        ydl_params = self._get_ydl_params(high_res=high_res)
        if format_id:
            ydl_params["format"] = format_id
        content = self.downloader.download_to_bytes(url, ydl_params=ydl_params)

        va = VideoAttachment()
        va.content = content
        va.width = data.width
        va.height = data.height
        va.duration = data.duration
        va.thumbnail_url = data.thumbnail_url
        return va

    # -----------------------------

    # UTILS

    @classmethod
    def check_url_is_video(cls, url: str):
        parsed = urlparse(url)
        if parsed.hostname == "vkvideo.ru" and cls.CLIP_URL_RE.search(parsed.path):
            return
        if cls.VIDEO_URL_RE.search(parsed.path):
            return
        z_param = dict(parse_qsl(parsed.query)).get("z")
        if z_param and cls.VIDEO_URL_RE.search(z_param):
            return
        raise PWarning("Ссылка должна быть на видео, не на канал")

    @staticmethod
    def clear_url(url: str) -> str:
        parsed = urlparse(url)
        query = dict(parse_qsl(parsed.query))
        query.pop("list", None)
        query.pop("section", None)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(query), ""))

    @staticmethod
    def _get_channel_id(info: dict) -> str:
        if info.get("uploader_id"):
            return str(info["uploader_id"])
        if info.get("channel_id"):
            return str(info["channel_id"])
        return str(info["id"]).split("_", 1)[0]

    @staticmethod
    def _filesize_key(_format: dict) -> int:
        return YtDlpVideoDownloader.filesize_key(_format)

    # -----------------------------

    # VIDEO DOWNLOAD HELPERS

    def _get_video_info(self, url: str) -> dict:
        video_info = self.downloader.extract_info(url, ydl_params=self._get_ydl_params(high_res=True))
        return self.downloader.get_first_playlist_entry(video_info)

    @classmethod
    def _get_ydl_params(cls, high_res: bool) -> dict:
        return {
            "format": cls._get_format_selector(high_res=high_res),
            "merge_output_format": "mp4",
            "noplaylist": True,
        }

    @classmethod
    def _get_format_selector(cls, high_res: bool) -> str:
        height_filter = "" if high_res else f"[height<={cls.DEFAULT_VIDEO_QUALITY_HEIGHT}]"
        return "/".join(
            [
                f"best[ext=mp4][vcodec!=none][acodec!=none]{height_filter}",
                f"bestvideo[ext=mp4][vcodec!=none]{height_filter}+bestaudio[ext=m4a]/bestvideo{height_filter}+bestaudio",
                f"best{height_filter}",
                "best",
            ],
        )

    @classmethod
    def _get_video_format(cls, video_info: dict, high_res: bool) -> dict:
        formats = video_info.get("formats") or []
        video_formats = [
            _format for _format in formats
            if _format.get("vcodec") != "none" and _format.get("height")
        ]
        if not video_formats:
            raise PWarning("Не получилось найти видеофайл")

        if not high_res:
            limited_video_formats = [
                _format for _format in video_formats
                if _format.get("height") <= cls.DEFAULT_VIDEO_QUALITY_HEIGHT
            ]
            if limited_video_formats:
                video_formats = limited_video_formats

        progressive_formats = [
            _format for _format in video_formats
            if _format.get("ext") == "mp4" and _format.get("acodec") != "none"
        ]
        if progressive_formats:
            video_formats = progressive_formats

        return sorted(
            video_formats,
            key=lambda _format: (_format.get("height") or 0, cls._filesize_key(_format)),
            reverse=True,
        )[0]

    @staticmethod
    def _prepare_ytdlp_error(error: yt_dlp.utils.DownloadError) -> PWarning:
        msg = error.msg
        if "Private video" in msg or "This video is private" in msg:
            return PWarning("Это приватное видео. Я не могу его скачать")
        if "Video unavailable" in msg:
            return PWarning("Это видео недоступно")
        if "Unsupported URL" in msg:
            return PWarning("Ссылка должна быть на видео, не на канал")
        return PWarning("Не смог найти видео по этой ссылке")

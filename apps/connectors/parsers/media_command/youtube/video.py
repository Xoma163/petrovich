import re
import shutil
import sys
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse, parse_qsl

import yt_dlp

from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.connectors.parsers.media_command.data import VideoData
from apps.shared.exceptions import PWarning
from apps.shared.utils.video.yt_dlp_video_downloader import YtDlpVideoDownloader


class _IncompleteYoutubeFormats(Exception):
    pass


class YoutubeVideo:
    DEFAULT_VIDEO_QUALITY_HIGHT = 720
    VIDEO_INFO_EXTRACTION_ATTEMPTS = 3
    ORIGINAL_AUDIO_LANGUAGE_PREFERENCE = 10
    ORIGINAL_AUDIO_LANGUAGE = "original"
    AUDIO_LANGUAGE_PATTERN = re.compile(r"^[a-z]{2,3}(?:-[a-z0-9]{2,8})*$", re.IGNORECASE)
    DOMAIN = "youtube.com"
    URL = f"https://{DOMAIN}"

    def __init__(self, log_filter: dict | None = None):
        self.log_filter = log_filter
        self.downloader = YtDlpVideoDownloader(ytdlp_error_handler=self._prepare_ytdlp_error)

    # SERVICE METHODS

    def get_video_info(
        self,
        url,
        high_res=False,
        _timedelta: float | None = None,
        audio_language: str | None = None,
    ) -> VideoData:
        audio_language = self._normalize_audio_language(audio_language)
        for attempt in range(self.VIDEO_INFO_EXTRACTION_ATTEMPTS):
            video_info = self._get_video_info(url)
            try:
                video, audio, filesize_mb = self._get_video_download_urls(
                    video_info,
                    high_res,
                    _timedelta,
                    allow_progressive=attempt == self.VIDEO_INFO_EXTRACTION_ATTEMPTS - 1,
                    audio_language=audio_language,
                )
                break
            except _IncompleteYoutubeFormats:
                continue

        return VideoData(
            filesize_mb=filesize_mb,
            video_download_url=video["url"] if video else None,
            audio_download_url=audio["url"] if audio else None,
            title=video_info["title"],
            duration=video_info.get("duration"),
            width=video.get("width"),
            height=video.get("height"),
            start_pos=str(video_info["section_start"]) if video_info.get("section_start") else None,
            end_pos=str(video_info["section_end"]) if video_info.get("section_end") else None,
            thumbnail_url=self._get_thumbnail(video_info),
            channel_id=video_info["channel_id"],
            video_id=video_info["id"],
            channel_title=video_info["channel"],
            is_short_video="/shorts/" in url or video_info.get("media_type") == "short",
            extra_data={
                "source_url": url,
                "video_format_id": video["format_id"],
                "fallback_video_format_ids": self._get_fallback_video_format_ids(video_info, video),
                "audio_format_id": audio["format_id"] if audio else None,
                "audio_language": audio_language,
            },
        )

    def download_video(self, data: VideoData) -> VideoAttachment:
        if not data.extra_data:
            raise ValueError
        source_url = data.extra_data.get("source_url")
        if not source_url:
            raise ValueError

        format_id = data.extra_data["video_format_id"]
        if audio_format_id := data.extra_data.get("audio_format_id"):
            format_id = f"{format_id}+{audio_format_id}/best[ext=mp4][vcodec!=none][acodec!=none]"
        ydl_params = self._get_ydl_params() | {"format": format_id, "merge_output_format": "mp4"}
        try:
            content = self.downloader.download_to_bytes(source_url, ydl_params=ydl_params)
        except PWarning as error:
            if not self._is_unavailable_format(error):
                raise
            for fallback_id in data.extra_data.get("fallback_video_format_ids", [])[:2]:
                fallback_format = fallback_id
                if audio_format_id:
                    fallback_format = f"{fallback_id}+{audio_format_id}/best[ext=mp4][vcodec!=none][acodec!=none]"
                try:
                    content = self.downloader.download_to_bytes(
                        source_url, ydl_params=ydl_params | {"format": fallback_format}
                    )
                    break
                except PWarning as fallback_error:
                    if not self._is_unavailable_format(fallback_error):
                        raise
                    error = fallback_error
            else:
                raise error

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
        t = dict(parse_qsl(urlparse(url).query)).get("t")
        if t:
            t = t.rstrip("s")
            h, m, s = str(timedelta(seconds=int(t))).split(":")
            if h:
                return f"{h}:{m}:{s}"
            return f"{m}:{s}"
        return ""

    @staticmethod
    def clear_url(url) -> str:
        parsed = urlparse(url)
        v = dict(parse_qsl(parsed.query)).get("v")
        res = f"{parsed.scheme}://{parsed.hostname}{parsed.path}"
        if v:
            res += f"?v={v}"
        return res

    # def _get_video_url(self, video_id) -> str:
    #     return f"{self.URL}/watch?v={video_id}"

    def check_url_is_video(self, url):
        url = self.clear_url(url)
        r = rf"(({self.DOMAIN}\/watch\?v=)|(youtu.be\/)|({self.DOMAIN}\/shorts\/))"
        res = re.findall(r, url)
        if not res:
            raise PWarning("Ссылка должна быть на видео, не на канал")

    @staticmethod
    def _filesize_key(x):
        if filesize := x.get("filesize"):
            return filesize
        if filesize_approx := x.get("filesize_approx"):
            return filesize_approx
        if filesize_approx_vbr := x.get("filesize_approx_vbr"):
            return filesize_approx_vbr * 100
        return 0

    @staticmethod
    def _get_thumbnail(info: dict) -> str | None:
        video_scale = info["width"] / info["height"]

        # Вертикальное видео
        if video_scale < 1:
            thumbnails = list(
                filter(
                    lambda x: x.get("width") and x.get("height") and x.get("width") / x.get("height") == video_scale,
                    info["thumbnails"],
                )
            )
        else:
            thumbnails = list(filter(lambda x: x["url"].endswith("maxresdefault.jpg"), info["thumbnails"]))

        if not thumbnails:
            return None

        try:
            return thumbnails[0]["url"]
        except IndexError, KeyError:
            return None

    # -----------------------------

    # VIDEO DOWNLOAD HELPERS

    @staticmethod
    def _is_unavailable_format(error: PWarning) -> bool:
        cause = error.__cause__
        if not isinstance(cause, yt_dlp.utils.DownloadError):
            return False
        message = cause.msg.lower()
        return any(text in message for text in ("http error 403", "http error 404", "requested format is not available"))

    @classmethod
    def _get_fallback_video_format_ids(cls, info: dict, selected: dict) -> list[str]:
        candidates = [
            video
            for video in info["formats"]
            if video.get("format_id") != selected["format_id"]
            and video.get("vbr")
            and video.get("ext") == "mp4"
            and video.get("vcodec") not in (None, "none", "vp9")
            and video["vcodec"].split(".", 1)[0] == selected["vcodec"].split(".", 1)[0]
            and (video.get("acodec") not in (None, "none")) == (selected.get("acodec") not in (None, "none"))
            and video.get("dynamic_range") == "SDR"
            and not video.get("__working")
            and video.get("width", 0) <= selected["width"]
            and video.get("height", 0) <= selected["height"]
        ]
        candidates.sort(
            key=lambda video: (
                video.get("protocol") == "https",
                video.get("width", 0) * video.get("height", 0),
                cls._filesize_key(video),
            ),
            reverse=True,
        )
        return [video["format_id"] for video in candidates[:2]]

    def _get_video_info(self, url: str) -> dict:
        video_info = self.downloader.extract_info(url, ydl_params=self._get_ydl_params())
        if video_info["media_type"] == "livestream":
            raise PWarning("Это стрим. Я не могу его скачать")
        return video_info

    @staticmethod
    def _get_ydl_params() -> dict:
        deno_path = shutil.which("deno")
        if not deno_path:
            executable_name = "deno.exe" if sys.platform == "win32" else "deno"
            venv_deno_path = Path(sys.executable).with_name(executable_name)
            if venv_deno_path.is_file():
                deno_path = str(venv_deno_path)

        return {
            "noplaylist": True,
            "js_runtimes": {"deno": {"path": deno_path} if deno_path else {}},
            "remote_components": ["ejs:npm", "ejs:github"],
        }

    @staticmethod
    def _prepare_ytdlp_error(error) -> PWarning:
        msg = error.msg
        if "Sign in to confirm your age" in msg:
            return PWarning("К сожалению видос доступен только залогиненым пользователям")
        if "Sign in to confirm you’re not a bot" in msg:
            return PWarning("Ютуб думает что я бот (да я бот). Попробуйте скачать видео позже")
        if "The following content is not available on this app" in msg:
            return PWarning("Это видео скачать не получится. ПАТАМУШТА")
        if "Requested format is not available." in msg:
            return PWarning("Ютуб отвалился. Создайте ишу, чтобы разраб обновил библиотечку плиз c:")
        if "This video has been removed for violating YouTube's Community Guidelines" in msg:
            return PWarning("Это видео было удалено за нарушение правил YouTube")
        return PWarning("Не смог найти видео по этой ссылке")

    @classmethod
    def _normalize_audio_language(cls, language: str | None) -> str | None:
        if language is None:
            return None
        language = language.strip().lower()
        if language == cls.ORIGINAL_AUDIO_LANGUAGE:
            return language
        if not language or not cls.AUDIO_LANGUAGE_PATTERN.fullmatch(language):
            raise PWarning("Неверный язык аудиодорожки. Пример: --lang-ru или --lang-en")
        return language

    @classmethod
    def _get_audio_format_by_language(cls, audio_formats: list[dict], language: str) -> dict | None:
        if language == cls.ORIGINAL_AUDIO_LANGUAGE:
            return next(
                (
                    audio_format
                    for audio_format in audio_formats
                    if audio_format.get("language_preference") == cls.ORIGINAL_AUDIO_LANGUAGE_PREFERENCE
                ),
                None,
            )

        def language_matches(audio_format: dict) -> bool:
            format_language = (audio_format.get("language") or "").lower()
            if "-" in language:
                return format_language == language
            return format_language == language or format_language.startswith(f"{language}-")

        return next((audio_format for audio_format in audio_formats if language_matches(audio_format)), None)

    @staticmethod
    def _get_available_audio_languages(audio_formats: list[dict]) -> str:
        languages = sorted({x["language"] for x in audio_formats if x.get("language")})
        return ", ".join(languages)

    def _get_video_download_urls(
        self,
        video_info: dict,
        high_res: bool = False,
        _timedelta: int | None = None,
        allow_progressive: bool = False,
        audio_language: str | None = None,
    ) -> tuple[dict, dict | None, int]:
        """
        Метод ищет видео которое максимально может скачать с учётом ограничением платформы
        return: video_format, audio_format, video_filesize
        """
        audio_formats = sorted(
            [x for x in video_info["formats"] if x.get("resolution") == "audio only"],  # abr
            key=self._filesize_key,
            reverse=True,
        )

        if not audio_formats and not allow_progressive:
            raise _IncompleteYoutubeFormats

        if audio_language:
            af = self._get_audio_format_by_language(audio_formats, audio_language)
            if not af:
                available_languages = self._get_available_audio_languages(audio_formats)
                available_text = f" Доступны: {available_languages}." if available_languages else ""
                raise PWarning(f'Аудиодорожка с языком "{audio_language}" не найдена.{available_text}')
        else:
            # YouTube may make an automatically dubbed track the viewer's default.
            # yt-dlp marks the source track with the highest language preference.
            af = self._get_audio_format_by_language(audio_formats, self.ORIGINAL_AUDIO_LANGUAGE)

        if not af and not audio_language:
            af = next(
                (x for x in audio_formats if (x.get("language") or "").lower().startswith("en")),
                None,
            )
        if not af and audio_formats and not audio_language:
            af = audio_formats[0]
        if not af and not allow_progressive:
            raise _IncompleteYoutubeFormats

        if not af:
            progressive_formats = [
                _format
                for _format in video_info["formats"]
                if _format.get("ext") == "mp4"
                and _format.get("vcodec") not in (None, "none")
                and _format.get("acodec") not in (None, "none")
                and _format.get("dynamic_range") == "SDR"
            ]
            if not progressive_formats:
                raise PWarning("Не получилось найти аудиодорожку")
            video_formats = sorted(progressive_formats, key=self._filesize_key, reverse=True)
        else:
            video_formats = list(
                filter(
                    lambda x: (
                        x.get("vbr")  # Это видео
                        and x.get("ext") == "mp4"  # С форматом mp4
                        and x.get("vcodec") not in ["vp9"]  # С кодеками которые поддерживают все платформы
                        and x.get("dynamic_range") == "SDR"  # В SDR качестве
                        and not x.get("__working")  # Без тестовых
                        # x.get('format_note')  # Имеют разрешение для просмотра (?)
                    ),
                    video_info["formats"],
                )
            )
            for _format in video_formats:
                _format["filesize_approx_vbr"] = video_info["duration"] * _format.get("vbr")
            video_formats = sorted(video_formats, key=self._filesize_key, reverse=True)

        if not video_formats:
            raise PWarning("Не получилось найти видеофайл")
        is_short_video = video_info["media_type"] == "short"

        vf = video_formats[0]
        if not high_res:
            for vf in video_formats:
                # Для коротких видео сравниваем в
                if is_short_video:
                    if int(vf["width"]) <= self.DEFAULT_VIDEO_QUALITY_HIGHT:
                        break
                else:
                    if int(vf["height"]) <= self.DEFAULT_VIDEO_QUALITY_HIGHT:
                        break

        # HLS variants of the same resolution can have stale manifests while the direct
        # HTTPS video stream is still available (notably for YouTube Shorts).
        if vf.get("protocol") == "m3u8_native":
            direct_formats = [
                _format
                for _format in video_formats
                if _format.get("protocol") == "https"
                and _format.get("width") == vf.get("width")
                and _format.get("height") == vf.get("height")
            ]
            if direct_formats:
                vf = direct_formats[0]

        video_filesize = (self._filesize_key(vf) + (self._filesize_key(af) if af else 0)) / 1024 / 1024
        return vf, af, video_filesize

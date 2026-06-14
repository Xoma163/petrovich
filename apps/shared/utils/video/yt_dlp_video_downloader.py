import os
from collections.abc import Callable
from glob import glob
from tempfile import mkstemp

import yt_dlp

from apps.shared.exceptions import PWarning


class _NothingLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


class YtDlpVideoDownloader:
    DEFAULT_CONCURRENT_FRAGMENT_DOWNLOADS = 10

    def __init__(
        self,
        ytdlp_error_handler: Callable[[yt_dlp.utils.DownloadError], PWarning] | None = None,
    ):
        self.ytdlp_error_handler = ytdlp_error_handler

    def extract_info(self, url: str, ydl_params: dict | None = None) -> dict:
        try:
            with yt_dlp.YoutubeDL(self._prepare_ydl_params(ydl_params)) as ydl:
                return ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as e:
            raise self._prepare_ytdlp_error(e) from e

    def download_to_bytes(self, url: str, ydl_params: dict | None = None) -> bytes:
        descriptor, tmp_video_file = mkstemp()
        os.close(descriptor)
        os.remove(tmp_video_file)

        try:
            params = self._prepare_ydl_params(
                {
                    "outtmpl": f"{tmp_video_file}.%(ext)s",
                    "force_overwrites": True,
                    "continuedl": False,
                    "concurrent_fragment_downloads": self.DEFAULT_CONCURRENT_FRAGMENT_DOWNLOADS,
                } | (ydl_params or {}),
            )

            with yt_dlp.YoutubeDL(params) as ydl:
                ydl.download([url])

            real_tmp_video_file = self._get_downloaded_file(tmp_video_file)
            if real_tmp_video_file is None:
                raise PWarning("Не получилось скачать видео")

            with open(real_tmp_video_file, "rb") as file:
                return file.read()
        except yt_dlp.utils.DownloadError as e:
            raise self._prepare_ytdlp_error(e) from e
        finally:
            self._remove_tmp_files(tmp_video_file)

    @staticmethod
    def get_first_playlist_entry(video_info: dict) -> dict:
        if video_info.get("_type") != "playlist":
            return video_info

        entries = [entry for entry in video_info.get("entries", []) if entry]
        if not entries:
            raise PWarning("Не смог найти видео по этой ссылке")
        return entries[0]

    @staticmethod
    def filesize_key(_format: dict) -> int:
        if filesize := _format.get("filesize"):
            return filesize
        if filesize_approx := _format.get("filesize_approx"):
            return filesize_approx
        if tbr := _format.get("tbr"):
            return int(tbr * 1024 * 1024 / 8)
        return 0

    @staticmethod
    def _prepare_ydl_params(ydl_params: dict | None = None) -> dict:
        return {
            "logger": _NothingLogger(),
            "quiet": True,
            "no_warnings": True,
        } | (ydl_params or {})

    @staticmethod
    def _get_downloaded_file(tmp_video_file: str) -> str | None:
        potential_filenames = [f"{tmp_video_file}.mp4", tmp_video_file, *glob(f"{tmp_video_file}.*")]
        for potential_filename in potential_filenames:
            if os.path.isfile(potential_filename) and os.path.getsize(potential_filename) > 0:
                return potential_filename
        return None

    @staticmethod
    def _remove_tmp_files(tmp_video_file: str):
        for potential_filename in [tmp_video_file, *glob(f"{tmp_video_file}.*")]:
            if os.path.exists(potential_filename):
                os.remove(potential_filename)

    def _prepare_ytdlp_error(self, error: yt_dlp.utils.DownloadError) -> PWarning:
        if self.ytdlp_error_handler:
            return self.ytdlp_error_handler(error)
        return PWarning("Не смог найти видео по этой ссылке")

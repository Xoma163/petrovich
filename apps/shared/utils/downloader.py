import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from tempfile import NamedTemporaryFile

import requests

from apps.connectors.utils import get_default_headers
from apps.shared.exceptions import PWarning
from apps.shared.utils.do_the_linux_command import do_the_linux_command


class Downloader:
    DEFAULT_CHUNK_SIZE = 2**24  # 16 mb

    def __init__(
        self,
        headers: dict | None = None,
        cookies: dict | None = None,
        log_filter: dict | None = None,
    ):
        self.headers = headers if headers else get_default_headers()
        self.cookies = cookies if cookies else {}
        self.log_filter = log_filter

    def _download_chunk(
        self,
        url: str,
        start: int,
        end: int,
    ) -> bytes:
        headers = {"Range": f"bytes={start}-{end}"}
        headers.update(self.headers)

        response = requests.get(url, headers=headers, stream=True, cookies=self.cookies)
        return response.content

    @staticmethod
    def open_file(path: str, delete_after_read: bool = False):
        with open(path, "rb") as file:
            content = file.read()
        if delete_after_read:
            if os.path.exists(path):
                os.remove(path)
        return content

    def download_in_parallel(self, url: str, chunk_size: int = DEFAULT_CHUNK_SIZE):
        response = requests.head(url, headers=self.headers, cookies=self.cookies)
        file_size = int(response.headers["Content-Length"])
        ranges = [(i, min(i + chunk_size - 1, file_size - 1)) for i in range(0, file_size, chunk_size)]

        with ThreadPoolExecutor() as executor:
            chunks = executor.map(lambda r: self._download_chunk(url, r[0], r[1]), ranges)
        return b"".join(chunks)

    def download_by_url(self, url: str):
        return requests.get(url, headers=self.headers, cookies=self.cookies).content

    def download_by_m3u8_url(self, m3u8_url: str, threads: int = 1, http_chunk_size: int | None = None) -> bytes:
        tmp_video_file = NamedTemporaryFile().name
        try:
            args = {
                "-N": threads,
                "-o": tmp_video_file,
                # '--cookies': os.path.join(BASE_DIR, 'secrets', 'youtube_cookies.txt')
            }
            if http_chunk_size is not None:
                args["--http-chunk-size"] = http_chunk_size
            args_str = " ".join([f"{x[0]} {x[1]}" for x in args.items()])
            command = f"yt-dlp {args_str} {m3u8_url}"
            try:
                _ = do_the_linux_command(command, log_filter=self.log_filter, check=True)
            except subprocess.CalledProcessError as e:
                raise PWarning("Не получилось скачать видео") from e

            potential_filename = f"{tmp_video_file}.mp4"
            if os.path.isfile(potential_filename):
                tmp_video_file = potential_filename

            if not os.path.isfile(tmp_video_file) or os.path.getsize(tmp_video_file) == 0:
                raise PWarning("Не получилось скачать видео")

            with open(tmp_video_file, "rb") as file:
                content = file.read()
        finally:
            if os.path.exists(tmp_video_file):
                os.remove(tmp_video_file)
        return content

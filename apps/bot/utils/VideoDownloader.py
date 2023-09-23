import os
from tempfile import NamedTemporaryFile

from apps.bot.utils.DoTheLinuxComand import do_the_linux_command


class VideoDownloader:
    @staticmethod
    def download(m3u8_url: str, threads: int = 1):
        tmp_video_file = NamedTemporaryFile().name
        try:
            do_the_linux_command(f"yt-dlp -N {threads} -o {tmp_video_file} {m3u8_url}")
            with open(tmp_video_file, 'rb') as file:
                video_content = file.read()
        finally:
            os.remove(tmp_video_file)
        return video_content

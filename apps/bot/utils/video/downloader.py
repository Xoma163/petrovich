import os
from tempfile import NamedTemporaryFile

from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.utils.do_the_linux_command import do_the_linux_command


class VideoDownloader:

    def __init__(self, video: VideoAttachment):
        self.video: VideoAttachment = video
        if self.video.m3u8_url is None:
            raise RuntimeError("m3u8_url not set")

    def download(self, threads: int = 1) -> bytes:
        tmp_video_file = NamedTemporaryFile().name
        try:
            do_the_linux_command(f"yt-dlp -N {threads} -o {tmp_video_file} {self.video.m3u8_url}")
            with open(tmp_video_file, 'rb') as file:
                video_content = file.read()
        finally:
            os.remove(tmp_video_file)
        return video_content

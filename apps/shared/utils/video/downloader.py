import os
from tempfile import NamedTemporaryFile

from apps.bot.core.messages.attachments.audio import AudioAttachment
from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.shared.utils.do_the_linux_command import do_the_linux_command


class VideoDownloader:

    def __init__(self, att: VideoAttachment | AudioAttachment):
        self.att: VideoAttachment = att

    def download_m3u8(self, threads: int = 1, http_chunk_size: int | None = None) -> bytes:
        if self.att.m3u8_url is None:
            raise RuntimeError("m3u8_url not set")

        tmp_video_file = NamedTemporaryFile().name
        try:
            args = {
                '-N': threads,
                '-o': tmp_video_file,
                # '--cookies': os.path.join(BASE_DIR, 'secrets', 'youtube_cookies.txt')
            }
            if http_chunk_size is not None:
                args['--http-chunk-size'] = http_chunk_size
            args_str = " ".join([f"{x[0]} {x[1]}" for x in args.items()])
            command = f"yt-dlp {args_str} {self.att.m3u8_url}"
            _ = do_the_linux_command(command)

            potential_filename = f"{tmp_video_file}.mp4"
            if os.path.isfile(potential_filename):
                tmp_video_file = potential_filename

            with open(tmp_video_file, 'rb') as file:
                video_content = file.read()
        finally:
            os.remove(tmp_video_file)
        return video_content

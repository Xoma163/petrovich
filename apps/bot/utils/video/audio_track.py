from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.utils.do_the_linux_command import do_the_linux_command
from apps.bot.utils.video.video_common import VideoCommon


class AudioTrack(VideoCommon):
    CHUNK_SIZE = 2 ** 26  # 64mb

    def __init__(self, video: VideoAttachment):
        super().__init__()

        self.video = video

    def get_audio_track(self) -> bytes:
        try:
            self._place_file(self.tmp_video_file, self.video)
            self._get_audio_track()
        finally:
            self.close_file(self.tmp_video_file)
        audio = self._get_video_bytes(self.tmp_output_file)
        self.close_all()
        return audio

    def _get_audio_track(self):
        args = [
            "ffmpeg6",
            "-i", self.tmp_video_file.name,
            "-vn", "-c:a", "aac",
            "-b:a", "192k",
            "-f", "adts",
            "-y",
            self.tmp_output_file.name,
        ]
        cmd = " ".join(args)
        res = do_the_linux_command(cmd)
        print()

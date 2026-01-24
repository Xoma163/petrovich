from apps.bot.core.messages.attachments.link import LinkAttachment
from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.shared.utils.do_the_linux_command import do_the_linux_command
from apps.shared.utils.video.video_common import VideoCommon


class VideoTrimmer(VideoCommon):
    def __init__(self, video: VideoAttachment | LinkAttachment | None):
        super().__init__()
        self.video = video

    def trim(self, start_pos, end_pos=None) -> bytes:
        try:
            self._place_file(self.tmp_video_file, self.video)

            cmd = [f"ffmpeg6 -i {self.tmp_video_file.name} -ss {start_pos}"]
            if end_pos:
                cmd.append(f"-to {end_pos}")
            cmd.append(f"-f mp4 -y {self.tmp_output_file.name}")
            cmd = " ".join(cmd)
            do_the_linux_command(cmd)

            file_bytes = self._get_video_bytes(self.tmp_output_file)
        finally:
            self.close_all()
        return file_bytes

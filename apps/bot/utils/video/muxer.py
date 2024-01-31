from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.utils.do_the_linux_command import do_the_linux_command
from apps.bot.utils.video.video_common import VideoCommon


class AudioVideoMuxer(VideoCommon):

    def __init__(self, video: VideoAttachment, audio: AudioAttachment):
        super().__init__()
        self.video: VideoAttachment = video
        self.audio: AudioAttachment = audio

    def mux(self):
        try:
            self._place_file(self.tmp_video_file, self.video)
            self._place_file(self.tmp_audio_file, self.audio)

            self._mux()
        finally:
            self.close_file(self.tmp_video_file)
            self.close_file(self.tmp_audio_file)
        video = self._get_video_bytes(self.tmp_output_file)
        self.close_all()
        return video

    def _mux(self):
        do_the_linux_command(
            f"ffmpeg6 -i {self.tmp_video_file.name} -i {self.tmp_audio_file.name} -c:v copy -c:a copy -strict -2 -f mp4 -y {self.tmp_output_file.name}"
        )

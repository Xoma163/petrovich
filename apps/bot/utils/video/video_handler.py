from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.link import LinkAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.utils.video.audio_track import AudioTrack
from apps.bot.utils.video.muxer import AudioVideoMuxer
from apps.bot.utils.video.trimmer import VideoTrimmer


class VideoHandler:
    AUDIO_ERROR = "Video must be provided"
    AUDIO_CONTENT_ERROR = "Audio content must be provided"
    VIDEO_ERROR = "Video must be provided"
    VIDEO_CONTENT_ERROR = "Video must be provided"
    VIDEO_OR_AUDIO_ERROR = "Video or audio must be provided"

    def __init__(
            self,
            video: VideoAttachment | LinkAttachment | None = None,
            audio: AudioAttachment = None
    ):
        self.video: VideoAttachment | LinkAttachment | None = video
        self.audio: AudioAttachment = audio

    def _check_video_content(self):
        if not self.video:
            raise RuntimeError(self.VIDEO_ERROR)
        if not self.video.content:
            raise RuntimeError(self.VIDEO_CONTENT_ERROR)

    def _check_audio_content(self):
        if not self.audio:
            raise RuntimeError(self.AUDIO_ERROR)
        if not self.audio.content:
            raise RuntimeError(self.AUDIO_CONTENT_ERROR)

    def check_video_and_audio(self):
        self._check_video_content()
        self._check_audio_content()

    def check_video_or_audio(self):
        for check in (self._check_video_content, self._check_audio_content):
            try:
                check()
                return
            except RuntimeError:
                continue
        raise RuntimeError(self.VIDEO_OR_AUDIO_ERROR)

    def mux(self) -> bytes:
        self.check_video_and_audio()

        avm = AudioVideoMuxer(self.video, self.audio)
        return avm.mux()

    def trim(self, start_pos, end_pos=None) -> bytes:
        self.check_video_or_audio()

        att = self.video if self.video else self.audio
        vt = VideoTrimmer(att)
        return vt.trim(start_pos, end_pos)

    def get_audio_track(self) -> bytes:
        self._check_video_content()

        at = AudioTrack(self.video)
        return at.get_audio_track()

    # def download(self, threads=10) -> bytes:
    #     if not self.video:
    #         raise RuntimeError(self.VIDEO_ERROR)
    #
    #     vd = VideoDownloader(self.video)
    #     if self.video.m3u8_url:
    #         return vd.download_m3u8(threads=threads)
    #     raise ValueError

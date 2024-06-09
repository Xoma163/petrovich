from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.link import LinkAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.utils.video.audio_track import AudioTrack
from apps.bot.utils.video.downloader import VideoDownloader
from apps.bot.utils.video.muxer import AudioVideoMuxer
from apps.bot.utils.video.trimmer import VideoTrimmer


class VideoHandler:
    VIDEO_ERROR = "Video must be provided"
    VIDEO_OR_AUDIO_ERROR = "Video or audio must be provided"
    def __init__(
            self,
            video: VideoAttachment | LinkAttachment | None = None,
            audio: AudioAttachment = None
    ):
        self.video: VideoAttachment | LinkAttachment | None = video
        self.audio: AudioAttachment = audio

    def mux(self) -> bytes:
        if not self.video:
            raise RuntimeError(self.VIDEO_ERROR)
        if not self.audio:
            raise RuntimeError(self.VIDEO_ERROR)

        avm = AudioVideoMuxer(self.video, self.audio)
        return avm.mux()

    def trim(self, start_pos, end_pos=None) -> bytes:
        if not self.video and not self.audio:
            raise RuntimeError(self.VIDEO_OR_AUDIO_ERROR)

        att = self.video if self.video else self.audio
        vt = VideoTrimmer(att)
        return vt.trim(start_pos, end_pos)

    def get_audio_track(self) -> bytes:
        if not self.video:
            raise RuntimeError(self.VIDEO_ERROR)

        at = AudioTrack(self.video)
        return at.get_audio_track()

    def download(self, threads=10) -> bytes:
        if not self.video:
            raise RuntimeError(self.VIDEO_ERROR)

        vd = VideoDownloader(self.video)
        return vd.download(threads=threads)

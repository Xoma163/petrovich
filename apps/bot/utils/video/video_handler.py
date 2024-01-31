from typing import Optional, Union

from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.link import LinkAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.utils.video.audio_track import AudioTrack
from apps.bot.utils.video.downloader import VideoDownloader
from apps.bot.utils.video.muxer import AudioVideoMuxer
from apps.bot.utils.video.trimmer import VideoTrimmer


class VideoHandler:
    def __init__(
            self,
            video: Optional[Union[VideoAttachment, LinkAttachment]] = None,
            audio: AudioAttachment = None
    ):
        self.video: Optional[Union[VideoAttachment, LinkAttachment]] = video
        self.audio: AudioAttachment = audio

    def mux(self) -> bytes:
        if not self.video:
            raise RuntimeError("video must be provided")
        if not self.audio:
            raise RuntimeError("audio must be provided")

        avm = AudioVideoMuxer(self.video, self.audio)
        return avm.mux()

    def trim(self, start_pos, end_pos=None) -> bytes:
        if not self.video or self.audio:
            raise RuntimeError("video or audio must be provided")

        att = self.video if self.video else self.audio
        vt = VideoTrimmer(att)
        return vt.trim(start_pos, end_pos)

    def get_audio_track(self) -> bytes:
        if not self.video:
            raise RuntimeError("video must be provided")

        at = AudioTrack(self.video)
        return at.get_audio_track()

    def download(self, threads=10) -> bytes:
        if not self.video:
            raise RuntimeError("video must be provided")

        vd = VideoDownloader(self.video)
        return vd.download(threads=threads)

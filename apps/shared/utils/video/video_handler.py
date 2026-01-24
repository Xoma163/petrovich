import subprocess
import tempfile
from pathlib import Path

from apps.bot.core.messages.attachments.audio import AudioAttachment
from apps.bot.core.messages.attachments.link import LinkAttachment
from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.shared.utils.video.audio_track import AudioTrack
from apps.shared.utils.video.muxer import AudioVideoMuxer
from apps.shared.utils.video.trimmer import VideoTrimmer


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

    def get_preview(self, second: float = 1.0, max_width=120, max_height=90) -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(self.video.content)
            tmp_path = tmp.name
        out_path = tmp_path + ".jpg"
        try:
            cmd = [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-ss", f"{second}",
                "-i", tmp_path,
                "-frames:v", "1",
                "-vf", f"scale={max_width}:{max_height}:flags=lanczos",
                "-q:v", "2",
                out_path
            ]
            subprocess.check_call(cmd)
            return Path(out_path).read_bytes()
        finally:
            Path(tmp_path).unlink()
            Path(out_path).unlink()

    # def download(self, threads=10) -> bytes:
    #     if not self.video:
    #         raise RuntimeError(self.VIDEO_ERROR)
    #
    #     vd = VideoDownloader(self.video)
    #     if self.video.m3u8_url:
    #         return vd.download_m3u8(threads=threads)
    #     raise ValueError

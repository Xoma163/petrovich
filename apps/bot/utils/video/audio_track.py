from tempfile import NamedTemporaryFile

from requests import Response

from apps.bot.utils.do_the_linux_command import do_the_linux_command


class AudioTrack:
    CHUNK_SIZE = 2 ** 26  # 64mb

    def __init__(self):
        self.tmp_video_file = NamedTemporaryFile()
        self.tmp_audio_file = NamedTemporaryFile()

    def get_audio_track(self, video_content) -> bytes:
        try:
            self._place_files(video_content)
            self._get_audio_track()
        finally:
            self._delete_video_file()
        return self._get_video_bytes()

    def _place_files(self, video_content):
        self._place_file(self.tmp_video_file.name, video_content)

    def _place_file(self, path, content):
        with open(path, 'wb') as file:
            if isinstance(content, Response):
                response = content
                file.write(next(response.iter_content(chunk_size=self.CHUNK_SIZE)))
                for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                    file.write(chunk)
            else:
                file.write(content)

    def _get_audio_track(self):
        do_the_linux_command(f"ffmpeg6 -i {self.tmp_video_file.name} -c:a copy -f adts -y {self.tmp_audio_file.name}")

    def _delete_video_file(self):
        self.tmp_video_file.close()

    def _delete_audio_file(self):
        self.tmp_audio_file.close()

    def _get_video_bytes(self):
        try:
            with open(self.tmp_audio_file.name, 'rb') as file:
                file_bytes = file.read()
        finally:
            self._delete_audio_file()
        return file_bytes

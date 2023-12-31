from tempfile import NamedTemporaryFile

from requests import Response

from apps.bot.utils.do_the_linux_command import do_the_linux_command


class AudioVideoMuxer:
    CHUNK_SIZE = 2 ** 26  # 64mb

    def __init__(self):
        self.tmp_video_file = NamedTemporaryFile()
        self.tmp_audio_file = NamedTemporaryFile()
        self.tmp_output_file = NamedTemporaryFile()

    def mux(self, video_content, audio_content):
        try:
            self._place_files(video_content, audio_content)
            self._mux_video_and_audio()
        finally:
            self._delete_video_audio_files()
        return self._get_video_bytes()

    def _place_files(self, video_content, audio_content):
        self._place_file(self.tmp_video_file.name, video_content)
        self._place_file(self.tmp_audio_file.name, audio_content)

    def _place_file(self, path, content):
        with open(path, 'wb') as file:
            if isinstance(content, Response):
                response = content
                file.write(next(response.iter_content(chunk_size=self.CHUNK_SIZE)))
                for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                    file.write(chunk)
            else:
                file.write(content)

    def _mux_video_and_audio(self):
        do_the_linux_command(
            f"ffmpeg6 -i {self.tmp_video_file.name} -i {self.tmp_audio_file.name} -c:v copy -c:a copy -strict -2 -f mp4 -y {self.tmp_output_file.name}")

    def _delete_video_audio_files(self):
        self.tmp_video_file.close()
        self.tmp_audio_file.close()

    def _delete_output_file(self):
        self.tmp_output_file.close()

    def _get_video_bytes(self):
        try:
            with open(self.tmp_output_file.name, 'rb') as file:
                file_bytes = file.read()
        finally:
            self._delete_output_file()
        return file_bytes

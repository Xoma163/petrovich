from tempfile import NamedTemporaryFile

from apps.bot.utils.DoTheLinuxComand import do_the_linux_command


class AudioVideoMuxer:
    def __init__(self):
        self.tmp_video_file = NamedTemporaryFile()
        self.tmp_audio_file = NamedTemporaryFile()
        self.tmp_output_file = NamedTemporaryFile()

    def mux(self, video_url, audio_url):
        self._place_files(video_url, audio_url)
        self._mux_video_and_audio()
        return self._get_video_bytes()

    def _place_files(self, video_content, audio_content):
        with open(self.tmp_video_file.name, 'wb') as file:
            file.write(video_content)
        with open(self.tmp_audio_file.name, 'wb') as file:
            file.write(audio_content)

    def _mux_video_and_audio(self):
        try:
            do_the_linux_command(
                f"ffmpeg6 -i {self.tmp_video_file.name} -i {self.tmp_audio_file.name} -c:v copy -c:a copy -strict -2 -f mp4 -y {self.tmp_output_file.name}")
        finally:
            self._delete_video_audio_files()

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

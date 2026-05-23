import subprocess
import types
from os import close, unlink
from tempfile import mkstemp

from apps.bot.core.messages.attachments.attachment import Attachment
from apps.shared.exceptions import PWarning
from apps.shared.utils.do_the_linux_command import do_the_linux_command


class VideoCommon:
    def __init__(self, log_filter: dict | None = None):
        self.log_filter = log_filter
        self.tmp_video_file = self._make_tmp_file()
        self.tmp_audio_file = self._make_tmp_file()
        self.tmp_output_file = self._make_tmp_file()

    @staticmethod
    def _make_tmp_file():
        descriptor, name = mkstemp()
        close(descriptor)
        return types.SimpleNamespace(name=name, closed=False)

    def _run_command(self, cmd: str, error_message: str = "Не получилось обработать видео"):
        try:
            do_the_linux_command(cmd, log_filter=self.log_filter, check=True)
        except subprocess.CalledProcessError as e:
            raise PWarning(error_message) from e

    @staticmethod
    def _place_file(file, att: Attachment):
        with open(file.name, "wb") as _file:
            content = att.content
            if isinstance(content, types.GeneratorType):
                for chunk in content:
                    _file.write(chunk)
            elif content is not None:
                _file.write(content)

    @staticmethod
    def close_file(file):
        if getattr(file, "closed", False):
            return
        file.closed = True
        try:
            unlink(file.name)
        except FileNotFoundError:
            pass

    def close_all(self):
        self.close_file(self.tmp_video_file)
        self.close_file(self.tmp_audio_file)
        self.close_file(self.tmp_output_file)

    def _get_video_bytes(self, file):
        try:
            with open(file.name, "rb") as _file:
                file_bytes = _file.read()
        finally:
            self.close_file(file)
        return file_bytes

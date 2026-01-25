import types
from tempfile import NamedTemporaryFile

from apps.bot.core.messages.attachments.attachment import Attachment


class VideoCommon:
    def __init__(self):
        self.tmp_video_file = NamedTemporaryFile()
        self.tmp_audio_file = NamedTemporaryFile()
        self.tmp_output_file = NamedTemporaryFile()

    @staticmethod
    def _place_file(file: type[NamedTemporaryFile], att: Attachment):
        with open(file.name, 'wb') as _file:
            if isinstance(att.content, types.GeneratorType):
                for chunk in att.content:
                    _file.write(chunk)
            else:
                _file.write(att.content)

    @staticmethod
    def close_file(file: type[NamedTemporaryFile]):
        file.close()

    def close_all(self):
        self.close_file(self.tmp_video_file)
        self.close_file(self.tmp_audio_file)
        self.close_file(self.tmp_output_file)

    def _get_video_bytes(self, file: type[NamedTemporaryFile]):
        try:
            with open(file.name, 'rb') as _file:
                file_bytes = _file.read()
        finally:
            self.close_file(file)
        return file_bytes

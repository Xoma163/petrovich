import types
from tempfile import NamedTemporaryFile

from apps.bot.classes.messages.attachments.attachment import Attachment


class VideoCommon:
    def __init__(self):
        self.tmp_video_file = NamedTemporaryFile()
        self.tmp_audio_file = NamedTemporaryFile()
        self.tmp_output_file = NamedTemporaryFile()

    @staticmethod
    def _place_file(file: NamedTemporaryFile, att: Attachment):
        with open(file.name, 'wb') as _file:
            content = att.download_content(stream=True)
            if isinstance(content, types.GeneratorType):
                for chunk in content:
                    _file.write(chunk)
            else:
                _file.write(content)

    @staticmethod
    def close_file(file: NamedTemporaryFile):
        file.close()

    def close_all(self):
        self.close_file(self.tmp_video_file)
        self.close_file(self.tmp_audio_file)
        self.close_file(self.tmp_output_file)

    def _get_video_bytes(self, file: NamedTemporaryFile):
        try:
            with open(file.name, 'rb') as _file:
                file_bytes = _file.read()
        finally:
            self.close_file(file)
        return file_bytes

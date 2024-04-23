from io import BytesIO

from pydub import AudioSegment

from apps.bot.classes.messages.attachments.audio import AudioAttachment


class AudioConverter:

    @classmethod
    def convert(cls, auido: AudioAttachment, _format: str) -> BytesIO:
        i = auido.get_bytes_io_content()
        i.seek(0)
        o = BytesIO()
        o.name = f"audio.{_format}"

        input_file_format = auido.ext
        if auido.ext == 'oga':
            input_file_format = 'ogg'
        AudioSegment.from_file(i, input_file_format).export(o, format=_format)
        return o

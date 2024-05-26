from io import BytesIO

from pydub import AudioSegment

from apps.bot.classes.messages.attachments.audio import AudioAttachment


class AudioConverter:

    @classmethod
    def convert(cls, audio: AudioAttachment, _format: str) -> BytesIO:
        """
        Преобразует из одного аудиоформата в другой
        Возаращает файл bytesio
        """
        # input
        i = audio.get_bytes_io_content()
        i.seek(0)

        # output
        o = BytesIO()
        o.name = f"audio.{audio.ext}"

        input_file_format = audio.ext
        if audio.ext == 'oga':
            input_file_format = 'ogg'
        audio = AudioSegment.from_file(i, input_file_format)
        audio.export(o, format=_format)
        # duration_seconds = len(audio) / 1000
        return o

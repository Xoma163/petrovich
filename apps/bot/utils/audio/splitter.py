from io import BytesIO

from pydub import AudioSegment

from apps.bot.core.messages.attachments.audio import AudioAttachment


class AudioSplitter:

    @classmethod
    def split(cls, audio: AudioAttachment, max_size_mb: float) -> list[BytesIO]:
        """
        Режет аудиофайл на чанки одинаковой длины (в мегабайтах)
        Возвращает список BytesIO
        """

        i = audio.get_bytes_io_content()
        i.seek(0)
        audio_segment = AudioSegment.from_file(i, audio.ext)

        max_size_bytes = max_size_mb * 1024 * 1024
        chunks = []

        chunk = AudioSegment.empty()
        for segment in audio_segment[::1000]:  # Обработка по 1 секунде
            if len(chunk.raw_data) + len(segment.raw_data) > max_size_bytes:
                chunks.append(chunk)
                chunk = AudioSegment.empty()
            chunk += segment

        if len(chunk.raw_data) > 0:
            chunks.append(chunk)

        audios = []
        for i, chunk in enumerate(chunks):
            o = BytesIO()
            o.name = f"audio_part_{i}.{audio.ext}"
            chunk.export(o, format="wav")
            audios.append(o)
        return audios

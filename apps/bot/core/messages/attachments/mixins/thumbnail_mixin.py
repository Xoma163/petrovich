import io

from PIL import Image

from apps.bot.core.messages.attachments.photo import PhotoAttachment


class ThumbnailMixin:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.thumbnail_url: str | None = None
        self.thumbnail: PhotoAttachment | None = None

    def set_thumbnail(self, content: bytes = None):
        if self.thumbnail_url is None and content is None:
            return

        thumb_file = PhotoAttachment()
        if content:
            thumb_file.parse(content)
        else:
            thumb_file.parse(self.thumbnail_url, guarantee_url=True)

        thumbnail = self.make_thumbnail(thumb_file, max_size=None)
        thumbnail_att = PhotoAttachment()
        thumbnail_att.parse(thumbnail)
        self.thumbnail = thumbnail_att

    @staticmethod
    def make_thumbnail(
            photo_attachment: PhotoAttachment,
            max_size: int | None = None,
    ) -> io.BytesIO:
        """
        Центрирование изображение с блюром в пустотах
        Используется для получения thumbnail
        Принудительно переводится в jpeg
        """

        image_bytes = io.BytesIO(photo_attachment.download_content())
        image = Image.open(image_bytes).convert("RGB")
        # Проверяем, нужно ли уменьшить изображение
        if max_size and (image.width > max_size or image.height > max_size):
            # Вычисляем коэффициент уменьшения
            ratio = min(max_size / image.width, max_size / image.height)
            # Уменьшаем изображение пропорционально
            image = image.resize((int(image.width * ratio), int(image.height * ratio)), Image.Resampling.LANCZOS)

        # Преобразуем результат в JPEG
        jpeg_image_io = io.BytesIO()
        image.save(jpeg_image_io, format='JPEG')
        jpeg_image_io.seek(0)

        return jpeg_image_io

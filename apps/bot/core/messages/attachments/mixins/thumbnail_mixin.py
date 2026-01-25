import io

from PIL import Image

from apps.bot.core.messages.attachments.photo import PhotoAttachment


class ThumbnailMixin:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.thumbnail: PhotoAttachment | None = None
        self.thumbnail_url: str | None = None
        self.thumbnail_bytes: bytes | None = None

    def set_thumbnail(self, max_size: int = 320, _format="JPEG"):
        if self.thumbnail:
            return

        if not self.thumbnail_url and not self.thumbnail_bytes:
            return

        thumb_file = PhotoAttachment()
        thumb_file.parse(_bytes=self.thumbnail_bytes, url=self.thumbnail_url)

        thumbnail_bytes = self.make_thumbnail(thumb_file, max_size=max_size, _format=_format)
        thumbnail_att = PhotoAttachment()
        thumbnail_att.content = thumbnail_bytes
        self.thumbnail = thumbnail_att

    @staticmethod
    def make_thumbnail(
            photo_attachment: PhotoAttachment,
            max_size: int | None = None,
            _format: str | None = None,
    ) -> bytes:
        """
        Центрирование изображение с блюром в пустотах
        Используется для получения thumbnail
        Принудительно переводится в jpeg
        """
        from apps.shared.utils.utils import convert_pil_image_to_bytes

        image_bytes = io.BytesIO(photo_attachment.download_content())
        image = Image.open(image_bytes).convert("RGB")
        # Проверяем, нужно ли уменьшить изображение
        if max_size and (image.width > max_size or image.height > max_size):
            # Вычисляем коэффициент уменьшения
            ratio = min(max_size / image.width, max_size / image.height)
            # Уменьшаем изображение пропорционально
            image = image.resize((int(image.width * ratio), int(image.height * ratio)), Image.Resampling.LANCZOS)

        # Преобразуем результат в JPEG
        return convert_pil_image_to_bytes(image, _format=_format)

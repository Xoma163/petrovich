import io

from PIL import Image, ImageDraw

from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PWarning, PError
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.utils.utils import get_font_by_path, get_image_size_by_text
from petrovich.settings import env


class EveryPixel(API):
    IMAGE_QUALITY_URL = 'https://api.everypixel.com/v1/quality_ugc'
    IMAGE_FACES_URL = 'https://api.everypixel.com/v1/faces'
    CLIENT_ID = env.str("EVERYPIXEL_CLIENT_ID")
    CLIENT_SECRET = env.str("EVERYPIXEL_CLIENT_SECRET")

    RATE_LIMIT_ERROR = 'ratelimit exceeded 100 requests per 86400 seconds'

    def get_image_quality_by_file(self, file) -> dict:
        data = {'data': file}
        r = self.requests.post(self.IMAGE_QUALITY_URL, files=data, auth=(self.CLIENT_ID, self.CLIENT_SECRET)).json()
        return r

    def get_image_quality(self, _bytes) -> str:
        r = self.get_image_quality_by_file(_bytes)

        if r['status'] != 'ok':
            raise PError("Ошибка")
        return f"{round(r['quality']['score'] * 100, 2)}%"

    def get_faces_on_photo_by_file(self, file) -> dict:
        data = {
            'data': file
        }
        r = self.requests.post(self.IMAGE_FACES_URL, files=data, auth=(self.CLIENT_ID, self.CLIENT_SECRET)).json()
        return r

    def get_faces_on_photo(self, att: PhotoAttachment) -> PhotoAttachment:
        att.download_content()
        r = self.get_faces_on_photo_by_file(att.content)

        if r['status'] == 'error':
            if r['message'] == self.RATE_LIMIT_ERROR:
                raise PWarning("Сегодняшний лимит исчерпан")
            raise PError("Ошибка получения возраста на изображении")
        if r['status'] != "ok":
            raise PError("Ошибка. Статус не ок((")
        faces = r['faces']
        if len(faces) == 0:
            raise PWarning("Не нашёл лиц на фото")
        return self.draw_on_image(att.content, faces)

    @staticmethod
    def draw_on_image(image_bytes: bytes, faces) -> PhotoAttachment:
        data = io.BytesIO(image_bytes)
        image = Image.open(data)
        draw = ImageDraw.Draw(image)

        width, height = image.size
        scale = width * height / 1920 / 1080
        scale = max(scale, 0.6)

        font_size = round(40 * scale)
        red_rect_thickness = round(3 * scale)
        text_stroke = round(3 * scale)

        font = get_font_by_path("consolas.ttf", font_size)

        # Рисуем прямоугольники
        for face in faces:
            bbox = face['bbox']
            age = round(face['age'])

            # Рисуем прямоугольник
            draw.rectangle(face['bbox'], outline='red', width=red_rect_thickness)

            # Определяем координаты правого нижнего угла и смещение текста
            right_x = bbox[2]
            bottom_y = bbox[3]
            text = str(age)

            text_width, text_height = get_image_size_by_text(text, font)

            x = right_x - text_width - red_rect_thickness * 2
            y = bottom_y - text_height - red_rect_thickness * 3

            # thicker border
            offsets = range(-text_stroke, text_stroke + 1)
            for dx in offsets:
                for dy in offsets:
                    draw.text(
                        (x + dx, y + dy),
                        text,
                        font=font,
                        fill="black"
                    )

            draw.text((x, y), text, font=font, fill="white")

        attachment = PhotoAttachment()
        attachment.parse(image)
        return attachment

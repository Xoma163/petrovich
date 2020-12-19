import io
from io import BytesIO

import requests
from PIL import Image

from apps.bot.classes.Demotivator import DemotivatorBuilder
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_attachments_from_attachments_or_fwd


class Demotivator(CommonCommand):
    def __init__(self):
        names = ["демотиватор"]
        help_text = "Демотиватор - создаёт демотиватор"
        detail_help_text = "Демотиватор (Изображения/Пересылаемое сообщение с изображением) (большой текст)[;маленький текст] - создаёт демотиватор. \n" \
                           "Разделитель текста ;"
        super().__init__(names, help_text, detail_help_text, args=1, attachments=['photo'])

    def start(self):
        image = get_attachments_from_attachments_or_fwd(self.event, 'photo')[0]

        texts = list(map(str.strip, self.event.original_args.split(';')))
        if not texts[0]:
            return "Первая фраза обязательно должна быть"

        if 'content' in image:
            base_image = Image.open(BytesIO(image['content']))
        elif 'private_download_url' in image:
            response = requests.get(image['private_download_url'])
            base_image = Image.open(BytesIO(response.content))
        else:
            raise PWarning("Нет картинки в сообщении")

        db = DemotivatorBuilder(base_image, *texts)
        demotivator = db.get_demotivator()
        img_byte_arr = io.BytesIO()
        demotivator.save(img_byte_arr, format="PNG")

        attachments = self.bot.upload_photos(img_byte_arr)
        return {"attachments": attachments}

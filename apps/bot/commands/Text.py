from apps.bot.APIs.OCR import OCRApi
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_attachments_from_attachments_or_fwd


class Text(CommonCommand):
    name = "текст"
    help_text = "распознаёт текст на изображении"
    help_texts = [
        "Текст (Изображения/Пересылаемое сообщение с изображением) [язык=rus] - распознаёт текст на изображении\n"
        'Язык нужно указывать в 3 символа. Пример - "eng", "rus", "fre", "ger" и так далее'
    ]
    attachments = ['photo']

    def start(self):
        lang = "rus"
        if self.event.args:
            lang = self.event.args[0]

        ocr_api = OCRApi()
        image = get_attachments_from_attachments_or_fwd(self.event, 'photo')[0]
        image = image['private_download_url'] or image['content']
        return ocr_api.recognize(image, lang)

from apps.bot.APIs.OCR import OCRApi
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_attachments_from_attachments_or_fwd


# ToDo: TG вложения
class Text(CommonCommand):
    def __init__(self):
        names = ["текст"]
        help_text = "Текст - распознаёт текст на изображении"
        detail_help_text = "Текст (Изображения/Пересылаемое сообщение с изображением) [язык=rus] - распознаёт текст на изображении\n" \
                           'Язык нужно указывать в 3 символа. Пример - "eng", "rus", "fre", "ger" и так далее'
        super().__init__(names, help_text, detail_help_text, platforms=['vk'], attachments=['photo'])

    def start(self):
        lang = "rus"
        if self.event.args:
            lang = self.event.args[0]

        google_ocr = OCRApi()
        image = get_attachments_from_attachments_or_fwd(self.event, 'photo')[0]
        return google_ocr.recognize(image['download_url'], lang)

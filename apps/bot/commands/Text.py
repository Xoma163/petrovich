from apps.bot.APIs.OCR import OCRApi
from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_attachments_from_attachments_or_fwd


class Text(CommonCommand):
    names = ["текст"]
    help_text = "Текст - распознаёт текст на изображении"
    detail_help_text = "Текст (Изображения/Пересылаемое сообщение с изображением) [язык=rus] - распознаёт текст на изображении\n" \
                       'Язык нужно указывать в 3 символа. Пример - "eng", "rus", "fre", "ger" и так далее'
    platforms = [Platform.VK, Platform.TG]
    attachments = ['photo']

    def start(self):
        lang = "rus"
        if self.event.args:
            lang = self.event.args[0]

        ocr_api = OCRApi()
        image = get_attachments_from_attachments_or_fwd(self.event, 'photo')[0]
        image = image['private_download_url'] or image['content']
        return ocr_api.recognize(image, lang)

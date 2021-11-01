from apps.bot.APIs.OCR import OCRApi
from apps.bot.classes.Command import Command
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment


class Text(Command):
    name = "текст"
    help_text = "распознаёт текст на изображении"
    help_texts = [
        "Текст (Изображения/Пересылаемое сообщение с изображением) [язык=rus] - распознаёт текст на изображении\n"
        'Язык нужно указывать в 3 символа. Пример - "eng", "rus", "fre", "ger" и так далее'
    ]
    attachments = [PhotoAttachment]

    def start(self):
        lang = "rus"
        if self.event.message.args:
            lang = self.event.message.args[0]

        ocr_api = OCRApi()
        image = self.event.get_all_attachments(self.event, [PhotoAttachment])[0]
        content = image.download_content()
        return ocr_api.recognize(content, lang)

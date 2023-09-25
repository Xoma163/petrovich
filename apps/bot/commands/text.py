from apps.bot.api.ocr import OCR
from apps.bot.classes.command import Command
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Text(Command):
    name = "текст"
    help_text = "распознаёт текст на изображении"
    help_texts = [
        "Текст (Изображения/Пересылаемое сообщение с изображением) [язык=rus] - распознаёт текст на изображении"
    ]
    help_texts_extra = 'Язык нужно указывать в 3 символа. Пример - "eng", "rus", "fre", "ger" и так далее'
    attachments = [PhotoAttachment]

    def start(self) -> ResponseMessage:
        lang = "rus"
        if self.event.message.args:
            lang = self.event.message.args[0]

        ocr_api = OCR()
        image = self.event.get_all_attachments(PhotoAttachment)[0]
        content = image.download_content(self.event.peer_id)
        answer = ocr_api.recognize(content, lang)
        return ResponseMessage(ResponseMessageItem(text=answer))

from apps.bot.api.everypixel import EveryPixel
from apps.bot.classes.command import Command
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class EstimatePhoto(Command):
    name = "оцени"
    names = ["оценить"]
    help_text = "оценить качество фотографии"
    help_texts = ["(Изображение/Пересылаемое сообщение с изображением) - оценивает качество изображения"]
    attachments = [PhotoAttachment]

    def start(self) -> ResponseMessage:
        image = self.event.get_all_attachments(PhotoAttachment)[0]

        everypixel_api = EveryPixel()
        image_quality = everypixel_api.get_image_quality(image.download_content(self.event.peer_id))
        answer = f"Качество картинки - {image_quality}"
        return ResponseMessage(ResponseMessageItem(text=answer))

from apps.bot.APIs.EveryPixelAPI import EveryPixelAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment


class EstimatePhoto(Command):
    name = "оцени"
    names = ["оценить"]
    help_text = "оценить качество фотографии"
    help_texts = ["(Изображение/Пересылаемое сообщение с изображением) - оценивает качество изображения"]
    platforms = [Platform.VK, Platform.TG]
    attachments = [PhotoAttachment]

    def start(self):
        image = self.event.get_all_attachments(PhotoAttachment)[0]

        everypixel_api = EveryPixelAPI()
        image_quality = everypixel_api.get_image_quality(image.get_download_url())
        return f"Качество картинки - {image_quality}"

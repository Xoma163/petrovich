from apps.bot.APIs.EveryPixelAPI import EveryPixelAPI
from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_attachments_from_attachments_or_fwd


class EstimatePhoto(CommonCommand):
    name = "оцени"
    names = ["оценить"]
    help_text = "оценить качество фотографии"
    help_texts = ["(Изображение/Пересылаемое сообщение с изображением) - оценивает качество изображения"]
    platforms = [Platform.VK, Platform.TG]
    attachments = ['photo']

    def start(self):
        image = get_attachments_from_attachments_or_fwd(self.event, 'photo')[0]

        everypixel_api = EveryPixelAPI()
        image = image['private_download_url'] or image['content']
        image_quality = everypixel_api.get_image_quality(image)
        return f"Качество картинки - {image_quality}"

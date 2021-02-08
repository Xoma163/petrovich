from apps.bot.APIs.EveryPixelAPI import EveryPixelAPI
from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_attachments_from_attachments_or_fwd


class EstimatePhoto(CommonCommand):
    names = ["оцени", "оценить"]
    help_text = "Оцени - оценить качество фотографии"
    detail_help_text = "Оцени (Изображение/Пересылаемое сообщение с изображением) - оценивает качество изображения"
    platforms = [Platform.VK, Platform.TG]
    attachments = ['photo']

    def start(self):
        image = get_attachments_from_attachments_or_fwd(self.event, 'photo')[0]

        everypixel_api = EveryPixelAPI()
        image = image['download_url'] or image['content']
        image_quality = everypixel_api.get_image_quality(image)
        return f"Качество картинки - {image_quality}"

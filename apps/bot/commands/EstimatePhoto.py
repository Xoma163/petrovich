from apps.bot.APIs.EveryPixelAPI import EveryPixelAPI
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_attachments_from_attachments_or_fwd


# ToDo: TG вложения
class EstimatePhoto(CommonCommand):
    def __init__(self):
        names = ["оцени", "оценить"]
        help_text = "Оцени - оценить качество фотографии"
        detail_help_text = "Оцени (Изображение/Пересылаемое сообщение с изображением) - оценивает качество изображения"
        super().__init__(names, help_text, detail_help_text, platforms=['vk', 'tg'], attachments=['photo'])

    def start(self):
        image = get_attachments_from_attachments_or_fwd(self.event, 'photo')[0]

        everypixel_api = EveryPixelAPI(image['download_url'])
        image_quality = everypixel_api.get_image_quality()
        return f"Качество картинки - {image_quality}"

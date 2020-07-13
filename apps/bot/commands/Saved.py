from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_attachments_from_attachments_or_fwd


class Saved(CommonCommand):
    def __init__(self):
        names = ["сохраненка", "перешли", "сохраненные"]
        help_text = "Сохранёнка (фотографии) - пересылает фотографии, чтобы их можно было сохранить в вк в сохранёнки"
        super().__init__(names, help_text, platforms=['vk'], enabled=False)

    def start(self):
        attachments = get_attachments_from_attachments_or_fwd(self.event, 'photo')
        if len(attachments) == 0:
            return "Не нашёл в сообщении фотографий"
        attachments_url = [attachment['download_url'] for attachment in attachments]
        attachments = self.bot.upload_photos(attachments_url)
        return {'attachments': attachments}

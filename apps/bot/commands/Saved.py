from apps.bot.classes.Consts import Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_attachments_from_attachments_or_fwd


class Saved(CommonCommand):
    names = ["сохраненка", "перешли", "сохраненные"]
    help_text = "Сохранёнка (фотографии) - пересылает фотографии, чтобы их можно было сохранить в вк в сохранёнки"
    platforms = [Platform.VK]
    enabled = False

    def start(self):
        attachments = get_attachments_from_attachments_or_fwd(self.event, 'photo')
        if len(attachments) == 0:
            raise PWarning("Не нашёл в сообщении фотографий")
        attachments_url = [attachment['private_download_url'] for attachment in attachments]
        attachments = self.bot.upload_photos(attachments_url)
        return {'attachments': attachments}

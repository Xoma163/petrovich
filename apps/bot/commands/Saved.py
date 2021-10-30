from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.utils.utils import get_attachments_from_attachments_or_fwd


class Saved(Command):
    name = "сохраненка"
    names = ["перешли", "сохраненные"]
    help_text = "Сохранёнка (фотографии) - пересылает фотографии, чтобы их можно было сохранить в вк в сохранёнки"
    platforms = [Platform.VK]
    enabled = False

    def start(self):
        attachments = get_attachments_from_attachments_or_fwd(self.event, [PhotoAttachment])
        if len(attachments) == 0:
            raise PWarning("Не нашёл в сообщении фотографий")
        attachments_url = [attachment.get_download_url() for attachment in attachments]
        attachments = self.bot.upload_photos(attachments_url, peer_id=self.event.peer_id)
        return {'attachments': attachments}

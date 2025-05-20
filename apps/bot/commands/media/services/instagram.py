from apps.bot.api.media.instagram import Instagram, InstagramAPIData, InstagramAPIDataItem
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning, PError
from apps.bot.commands.media.service import MediaServiceResponse, MediaService
from apps.bot.utils.utils import retry


class InstagramService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = Instagram(log_filter=self.event.log_filter)

    @retry(3, Exception, except_exceptions=(PWarning, PError), sleep_time=2)
    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        data: InstagramAPIData = self.service.get_data(url)

        attachments = []
        for item in data.items:
            if item.content_type == InstagramAPIDataItem.CONTENT_TYPE_IMAGE:
                attachment = self.bot.get_photo_attachment(
                    item.download_url,
                    peer_id=self.event.peer_id,
                    guarantee_url=True,
                    send_chat_action=False
                )
            elif item.content_type == InstagramAPIDataItem.CONTENT_TYPE_VIDEO:
                attachment = self.bot.get_video_attachment(item.download_url, peer_id=self.event.peer_id)
            else:
                continue
            attachments.append(attachment)

        text = "" if "/reel/" in url else data.caption
        return MediaServiceResponse(text=text, attachments=attachments)

    @classmethod
    def urls(cls) -> list[str]:
        return ['www.instagram.com', 'instagram.com']

    def check_sender_role(self) -> None:
        if not self.event.sender.check_role(Role.TRUSTED):
            raise PWarning("Медиа инстаграмм доступен только для доверенных пользователей")

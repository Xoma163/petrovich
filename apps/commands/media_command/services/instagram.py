from apps.bot.consts import RoleEnum
from apps.commands.media_command.service import MediaServiceResponse, MediaService
from apps.connectors.parsers.media_command.instagram import InstagramAPIDataItem, InstagramAPIData
from apps.connectors.parsers.media_command.instagram import InstagramParser
from apps.shared.exceptions import PWarning


class InstagramService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InstagramParser()

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
                attachment.thumbnail_url = item.thumbnail_url
                attachment.download_content()
            else:
                continue
            attachments.append(attachment)

        text = "" if "/reel/" in url else data.caption
        return MediaServiceResponse(text=text, attachments=attachments)

    @classmethod
    def urls(cls) -> list[str]:
        return ['www.instagram.com', 'instagram.com']

    def check_sender_role(self) -> None:
        if not self.event.sender.check_role(RoleEnum.TRUSTED):
            raise PWarning("Медиа инстаграмм доступен только для доверенных пользователей")

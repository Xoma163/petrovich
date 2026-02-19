from apps.commands.media_command.service import MediaServiceResponse, MediaService
from apps.connectors.parsers.media_command.pinterest import Pinterest, PinterestDataItem
from apps.shared.exceptions import PWarning


class PinterestService(MediaService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = Pinterest()

    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        data: PinterestDataItem = self.service.get_post_data(url)

        if data.content_type == PinterestDataItem.CONTENT_TYPE_VIDEO:
            attachment = self.bot.get_video_attachment(
                url=data.download_url,
                peer_id=self.event.peer_id,
                message_thread_id=self.event.message_thread_id,
            )
        elif data.content_type == PinterestDataItem.CONTENT_TYPE_IMAGE:
            attachment = self.bot.get_photo_attachment(
                url=data.download_url,
                send_chat_action=False
            )
        elif data.content_type == PinterestDataItem.CONTENT_TYPE_GIF:
            attachment = self.bot.get_gif_attachment(
                url=data.download_url,
                peer_id=self.event.peer_id,
                message_thread_id=self.event.message_thread_id,
            )
        else:
            raise PWarning(Pinterest.ERROR_MSG)

        return MediaServiceResponse(text=data.caption, attachments=[attachment])

    @classmethod
    def urls(cls) -> list[str]:
        return ['pinterest.com', 'ru.pinterest.com', 'www.pinterest.com', 'pin.it']

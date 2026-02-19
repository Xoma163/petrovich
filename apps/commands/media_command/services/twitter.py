from apps.bot.consts import RoleEnum
from apps.bot.core.chat_action_sender import ChatActionSender
from apps.bot.core.chat_actions import ChatActionEnum
from apps.commands.media_command.service import MediaServiceResponse, MediaService
from apps.connectors.parsers.media_command.twitter import Twitter
from apps.shared.decorators import retry
from apps.shared.exceptions import PWarning


class TwitterService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = Twitter(log_filter=self.event.log_filter)

    @retry(3, Exception, sleep_time=2, except_exceptions=(PWarning,))
    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActionSender(self.bot, ChatActionEnum.TYPING, self.event.peer_id, self.event.message_thread_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url: str) -> MediaServiceResponse:
        t_api = Twitter()
        data = t_api.get_post_data(url)

        if not data.items:
            return MediaServiceResponse(text=data.caption, attachments=[])

        attachments = []
        for att in data.items:
            if att.content_type == att.CONTENT_TYPE_VIDEO:
                video = self.bot.get_video_attachment(
                    url=att.download_url,
                    peer_id=self.event.peer_id,
                    message_thread_id=self.event.message_thread_id
                )
                video.download_content()
                attachments.append(video)
            elif att.content_type == att.CONTENT_TYPE_IMAGE:
                photo = self.bot.get_photo_attachment(
                    url=att.download_url,
                    send_chat_action=False
                )
                attachments.append(photo)

        return MediaServiceResponse(text=data.caption, attachments=attachments)

    @classmethod
    def urls(cls) -> list[str]:
        return ['www.twitter.com', 'twitter.com', 'x.com']

    def check_sender_role(self) -> None:
        if not self.event.sender.check_role(RoleEnum.TRUSTED):
            raise PWarning("Медиа твиттер доступен только для доверенных пользователей")

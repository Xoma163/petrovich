from apps.bot.api.media.twitter import Twitter
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.commands.media.service import MediaServiceResponse, MediaService
from apps.bot.utils.decorators import retry


class TwitterService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = Twitter(log_filter=self.event.log_filter)

    @retry(3, Exception, sleep_time=2, except_exceptions=(PWarning,))
    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        with ChatActivity(self.bot, ActivitiesEnum.TYPING, self.event.peer_id):
            return self._get_content_by_url(url)

    def _get_content_by_url(self, url: str) -> MediaServiceResponse:
        t_api = Twitter()
        data = t_api.get_post_data(url)

        if not data.items:
            return MediaServiceResponse(text=data.caption, attachments=[])

        attachments = []
        for att in data.items:
            if att.content_type == att.CONTENT_TYPE_VIDEO:
                video = self.bot.get_video_attachment(att.download_url, peer_id=self.event.peer_id)
                video.download_content(use_proxy=True)
                attachments.append(video)
            elif att.content_type == att.CONTENT_TYPE_IMAGE:
                photo = self.bot.get_photo_attachment(
                    att.download_url,
                    peer_id=self.event.peer_id,
                    send_chat_action=False
                )
                attachments.append(photo)

        return MediaServiceResponse(text=data.caption, attachments=attachments)

    @classmethod
    def urls(cls) -> list[str]:
        return ['www.twitter.com', 'twitter.com', 'x.com']

    def check_sender_role(self) -> None:
        if not self.event.sender.check_role(Role.TRUSTED):
            raise PWarning("Медиа твиттер доступен только для доверенных пользователей")

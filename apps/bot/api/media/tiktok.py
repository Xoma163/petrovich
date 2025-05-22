from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PWarning


class TikTokData:
    def __init__(
            self,
            video_url: str,
            description: str | None = None,
            thumbnail_url: str | None = None
    ):
        self.video_url = video_url
        self.description = description if description else None
        self.thumbnail_url = thumbnail_url if thumbnail_url else None


class TikTok(API):

    # ToDo: #950
    def get_video(self, url) -> TikTokData:
        raise PWarning("Временно не работает(( Я починю")

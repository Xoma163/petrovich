from requests.exceptions import ReadTimeout

from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PWarning
from petrovich.settings import env


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
    HEADERS = {
        "X-RapidAPI-Host": "tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com",
        "X-RapidAPI-Key": env.str("RAPID_API_KEY"),
    }
    URL = "https://tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com/vid/index"

    TRY_LATER_ERROR = "The request to the API has timed out. Please try again later, or if the issue persists, please contact the API provider"

    def get_video(self, url) -> TikTokData:
        try:
            r = self.requests.get(self.URL, params={'url': url}, headers=self.HEADERS, timeout=20).json()
        except ReadTimeout:
            raise PWarning("Ошибка на стороне API провайдера. Попробуйте позднее")

        if r.get('error'):
            raise PWarning("Ошибка API")

        if r.get("messages") and r['messages'] == self.TRY_LATER_ERROR:
            raise PWarning("Ошибка на стороне API провайдера. Попробуйте позднее")
        return TikTokData(video_url=r['video'][0], description=r['description'][0], thumbnail_url=r['cover'][0])

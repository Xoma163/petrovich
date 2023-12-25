from requests.exceptions import ReadTimeout

from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PWarning
from petrovich.settings import env


class TikTok(API):
    HEADERS = {
        "X-RapidAPI-Host": "tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com",
        "X-RapidAPI-Key": env.str("RAPID_API_KEY"),
    }
    URL = "https://tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com/vid/index"

    TRY_LATER_ERROR = "The request to the API has timed out. Please try again later, or if the issue persists, please contact the API provider"

    def get_video_url(self, url) -> str:
        try:
            r = self.requests.get(self.URL, params={'url': url}, headers=self.HEADERS, timeout=20).json()
        except ReadTimeout:
            raise PWarning("Ошибка на стороне API провайдера. Попробуйте позднее")

        if r.get("messages") and r['messages'] == self.TRY_LATER_ERROR:
            raise PWarning("Ошибка на стороне API провайдера. Попробуйте позднее")
        return r['video'][0]

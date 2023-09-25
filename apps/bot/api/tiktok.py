import logging

import requests

from apps.bot.classes.const.exceptions import PWarning
from petrovich.settings import env

logger = logging.getLogger('bot')


class TikTok:
    HEADERS = {
        "X-RapidAPI-Host": "tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com",
        "X-RapidAPI-Key": env.str("RAPID_API_KEY"),
    }
    URL = "https://tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com/vid/index"

    def get_video_url(self, url):
        try:
            r = requests.get(self.URL, params={'url': url}, headers=self.HEADERS, timeout=20).json()
        except requests.exceptions.ReadTimeout:
            raise PWarning("Ошибка на стороне API провайдера. Попробуйте позднее")

        logger.debug({"response": r})
        if r.get("messages") and r[
            'messages'] == "The request to the API has timed out. Please try again later, or if the issue persists, please contact the API provider":
            raise PWarning("Ошибка на стороне API провайдера. Попробуйте позднее")
        return r['video'][0]

import logging

import requests

from petrovich.settings import env

logger = logging.getLogger('bot')


class TikTokDownloaderAPI:
    HEADERS = {
        "X-RapidAPI-Host": "tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com",
        "X-RapidAPI-Key": env.str("RAPID_API_KEY"),
    }
    URL = "https://tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com/vid/index"

    def get_video_url(self, url):
        r = requests.get(self.URL, params={'url': url}, headers=self.HEADERS)
        logger.debug(r.content)
        return r.json()['video'][0]

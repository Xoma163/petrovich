import logging

import requests

from apps.bot.classes.const.exceptions import PWarning
from petrovich.settings import env

logger = logging.getLogger('responses')


class Facebook:
    _HOST = "facebook-reel-and-video-downloader.p.rapidapi.com"
    HEADERS = {
        "X-RapidAPI-Host": _HOST,
        "X-RapidAPI-Key": env.str("RAPID_API_KEY"),
    }
    URL = f"https://{_HOST}/app/main.php"

    def get_video_info(self, url):
        r = requests.get(self.URL, headers=self.HEADERS, params={"url": url}).json()
        logger.debug({"response": r})

        video_url = None
        if r['links']:
            video_url = r['links']['Download High Quality'] or r['links']['Download Low Quality']
        if not video_url:
            raise PWarning("Ссылка на фейсбук не является видео")
        return {
            "download_url": video_url,
            "caption": r.get('title')
        }

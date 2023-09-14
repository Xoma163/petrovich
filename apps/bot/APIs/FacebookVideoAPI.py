import logging

import requests

from apps.bot.classes.consts.Exceptions import PWarning
from petrovich.settings import env

logger = logging.getLogger('bot')


class FacebookVideoAPI:
    _HOST = "facebook-reel-and-video-downloader.p.rapidapi.com"
    HEADERS = {
        "X-RapidAPI-Host": _HOST,
        "X-RapidAPI-Key": env.str("RAPID_API_KEY"),
    }
    URL = f"https://{_HOST}/app/main.php"

    def __init__(self):
        self.caption = ""

    def get_content_url(self, url):
        r = requests.get(self.URL, headers=self.HEADERS, params={"url": url})
        logger.debug(r.content)
        r = r.json()
        if r.get('title'):
            self.caption = r['title']

        video_url = None
        if r['links']:
            video_url = r['links']['Download High Quality'] or r['links']['Download Low Quality']
        if not video_url:
            raise PWarning("Ссылка на инстаграмм не является видео/фото")
        return video_url

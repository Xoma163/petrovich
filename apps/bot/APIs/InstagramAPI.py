from urllib.parse import urlparse

import requests

from apps.bot.classes.consts.Exceptions import PWarning
from petrovich.settings import env


class InstagramAPI:
    CONTENT_TYPE_IMAGE = 'image'
    CONTENT_TYPE_VIDEO = 'video'

    _HOST = "instagram-scraper-20231.p.rapidapi.com"
    HEADERS = {
        "X-RapidAPI-Host": _HOST,
        "X-RapidAPI-Key": env.str("RAPID_API_KEY"),
    }
    URL = f"https://{_HOST}/postdetail"

    def __init__(self):
        self.content_type = None
        self.caption = ""

    def get_content_url(self, url):
        post_id = urlparse(url).path.strip('/').split('/')[1]
        r = requests.get(f"{self.URL}/{post_id}", headers=self.HEADERS).json()
        if 'video_versions' in r['data']:
            self.content_type = self.CONTENT_TYPE_VIDEO
            self.caption = r['data']['caption']['text'].strip()
            return r['data']['video_versions'][0]['url']
        elif 'image_versions2' in r['data']:
            self.content_type = self.CONTENT_TYPE_IMAGE
            self.caption = r['data']['caption']['text'].strip()
            return r['data']['image_versions2']['candidates'][0]['url']
        else:
            raise PWarning("Ссылка на инстаграмм не является видео/фото")

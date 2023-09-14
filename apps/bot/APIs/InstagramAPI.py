import logging
from urllib.parse import urlparse

import requests

from apps.bot.classes.consts.Exceptions import PWarning
from petrovich.settings import env

logger = logging.getLogger('bot')


class InstagramAPI:
    CONTENT_TYPE_IMAGE = 'image'
    CONTENT_TYPE_VIDEO = 'video'

    RAPID_API_KEY = env.str("RAPID_API_KEY")

    def __init__(self):
        self.content_type = None
        self.caption = ""

    def get_content_url(self, instagram_link):
        if '/stories/' in instagram_link:
            return self.get_story_data(instagram_link)
        elif '/reel/' in instagram_link:
            return self.get_post_data(instagram_link)
        elif '/p/' in instagram_link:
            return self.get_post_data(instagram_link)
        else:
            raise PWarning("Ссылка на инстаграмм не является видео/фото")

    def get_story_data(self, instagram_link):
        host = "rocketapi-for-instagram.p.rapidapi.com"
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": self.RAPID_API_KEY,
            "X-RapidAPI-Host": host,
        }
        url = f"https://{host}/instagram/media/get_info"

        _id = urlparse(instagram_link).path.strip('/').split('/')[-1]
        data = {"id": _id}

        r = requests.post(url, json=data, headers=headers)
        logger.debug(r.content)

        return self._parse_photo_or_video(r.json()['response']['body']['items'][0])

    def get_post_data(self, instagram_link):
        host = "instagram-scraper-20231.p.rapidapi.com"
        HEADERS = {
            "X-RapidAPI-Host": host,
            "X-RapidAPI-Key": self.RAPID_API_KEY,
        }
        URL = f"https://{host}/postdetail"

        post_id = urlparse(instagram_link).path.strip('/').split('/')[1]
        r = requests.get(f"{URL}/{post_id}", headers=HEADERS)
        logger.debug(r.content)

        return self._parse_photo_or_video(r.json()['data'])

    def _parse_photo_or_video(self, data):
        if 'video_versions' in data:
            self.content_type = self.CONTENT_TYPE_VIDEO
            self.caption = data.get('caption', {})
            self.caption = self.caption.get('text', "") if self.caption else None
            if not self.caption:
                self.caption = ""
            else:
                self.caption = self.caption.strip()
            return data['video_versions'][0]['url']
        elif 'image_versions2' in data:
            self.content_type = self.CONTENT_TYPE_IMAGE
            self.caption = data['caption']['text'].strip()
            return data['image_versions2']['candidates'][0]['url']
        else:
            raise PWarning("Ссылка на инстаграмм не является видео/фото")

import logging
from urllib.parse import urlparse

import requests

from apps.bot.classes.const.exceptions import PWarning
from petrovich.settings import env

logger = logging.getLogger('responses')


class Instagram:
    CONTENT_TYPE_IMAGE = 'image'
    CONTENT_TYPE_VIDEO = 'video'

    RAPID_API_KEY = env.str("RAPID_API_KEY")

    def __init__(self):
        self.content_type = None
        self.caption = ""

    def get_post_data(self, instagram_link) -> dict:
        if '/stories/' in instagram_link:
            return self._get_story_data(instagram_link)
        elif '/reel/' in instagram_link:
            return self._get_post_data(instagram_link)
        elif '/p/' in instagram_link:
            return self._get_post_data(instagram_link)
        else:
            raise PWarning("Ссылка на инстаграмм не является видео/фото")

    def _get_story_data(self, instagram_link) -> dict:
        host = "rocketapi-for-instagram.p.rapidapi.com"
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": self.RAPID_API_KEY,
            "X-RapidAPI-Host": host,
        }
        url = f"https://{host}/instagram/media/get_info"

        _id = urlparse(instagram_link).path.strip('/').split('/')[-1]
        data = {"id": _id}

        r = requests.post(url, json=data, headers=headers).json()
        logger.debug({"response": r})

        return self._parse_photo_or_video(r['response']['body']['items'][0])

    def _get_post_data(self, instagram_link) -> dict:
        host = "instagram-scraper-20231.p.rapidapi.com"
        HEADERS = {
            "X-RapidAPI-Host": host,
            "X-RapidAPI-Key": self.RAPID_API_KEY,
        }
        URL = f"https://{host}/postdetail"

        post_id = urlparse(instagram_link).path.strip('/').split('/')[1]
        r = requests.get(f"{URL}/{post_id}", headers=HEADERS).json()
        logger.debug({"response": r})

        return self._parse_photo_or_video(r['data'])

    def _parse_photo_or_video(self, data) -> dict:
        if 'video_versions' in data:
            return {
                "download_url": data['video_versions'][0]['url'],
                "content_type": self.CONTENT_TYPE_VIDEO,
                "caption": data.get('caption', {}).get("text", "").strip()
            }
        elif 'image_versions2' in data:
            return {
                "download_url": data['image_versions2']['candidates'][0]['url'],
                "content_type": self.CONTENT_TYPE_IMAGE,
                "caption": data.get('caption', {}).get("text", "").strip()
            }
        else:
            raise PWarning("Ссылка на инстаграмм не является видео/фото")

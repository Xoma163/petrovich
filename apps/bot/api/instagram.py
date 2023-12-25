from urllib.parse import urlparse

from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PWarning
from petrovich.settings import env


class Instagram(API):
    CONTENT_TYPE_IMAGE = 'image'
    CONTENT_TYPE_VIDEO = 'video'

    RAPID_API_KEY = env.str("RAPID_API_KEY")

    def __init__(self):
        super().__init__()
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

        r = self.requests.post(url, json=data, headers=headers).json()
        return self._parse_photo_or_video(r['response']['body']['items'][0])

    def _get_post_data(self, instagram_link) -> dict:
        host = "instagram-scraper-20231.p.rapidapi.com"
        headers = {
            "X-RapidAPI-Host": host,
            "X-RapidAPI-Key": self.RAPID_API_KEY,
        }
        url = f"https://{host}/postdetail"

        post_id = urlparse(instagram_link).path.strip('/').split('/')[1]
        r = self.requests.get(f"{url}/{post_id}", headers=headers).json()
        return self._parse_photo_or_video(r['data'])

    def _parse_photo_or_video(self, data) -> dict:
        caption = data.get('caption')
        if caption:
            caption = caption.get("text", "").strip()
        if 'video_versions' in data:
            return {
                "download_url": data['video_versions'][0]['url'],
                "content_type": self.CONTENT_TYPE_VIDEO,
                "caption": caption
            }
        elif 'image_versions2' in data:
            return {
                "download_url": data['image_versions2']['candidates'][0]['url'],
                "content_type": self.CONTENT_TYPE_IMAGE,
                "caption": caption
            }
        else:
            raise PWarning("Ссылка на инстаграмм не является видео/фото")

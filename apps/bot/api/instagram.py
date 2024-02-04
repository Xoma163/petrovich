from urllib.parse import urlparse

from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PWarning
from petrovich.settings import env


class InstagramAPIDataItem:
    CONTENT_TYPE_IMAGE = 'image'
    CONTENT_TYPE_VIDEO = 'video'

    def __init__(self, content_type, download_url):
        self.content_type = content_type
        self.download_url = download_url


class InstagramAPIData:
    def __init__(self):
        self.items: list[InstagramAPIDataItem] = []
        self.caption: str = ""

    def add_item(self, item: InstagramAPIDataItem):
        self.items.append(item)


class InstagramAPI(API):
    RAPID_API_KEY = env.str("RAPID_API_KEY")
    ERROR_MSG = "Ссылка на инстаграмм не является видео/фото"

    def get_post_data(self, instagram_link) -> InstagramAPIData:
        if '/stories/' in instagram_link:
            return self._get_story_data(instagram_link)
        elif '/reel/' in instagram_link:
            return self._get_post_data(instagram_link)
        elif '/p/' in instagram_link:
            return self._get_post_data(instagram_link)
        else:
            raise PWarning(self.ERROR_MSG)

    def _get_story_data(self, instagram_link) -> InstagramAPIData:
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
        return self._parse_response(r['response']['body']['items'][0])

    def _get_post_data(self, instagram_link) -> InstagramAPIData:
        host = "instagram-scraper-20231.p.rapidapi.com"
        headers = {
            "X-RapidAPI-Host": host,
            "X-RapidAPI-Key": self.RAPID_API_KEY,
        }
        url = f"https://{host}/postdetail"

        post_id = urlparse(instagram_link).path.strip('/').split('/')[1]
        r = self.requests.get(f"{url}/{post_id}", headers=headers).json()
        return self._parse_response(r['data'])

    def _parse_response(self, response) -> InstagramAPIData:
        data = InstagramAPIData()

        caption = response.get('caption')
        if caption:
            data.caption = caption.get("text", "").strip()

        if 'carousel_media' in response:
            for item in response['carousel_media']:
                data.add_item(self._parse_photo_or_video(item))
        else:
            data.add_item(self._parse_photo_or_video(response))

        return data

    def _parse_photo_or_video(self, item) -> InstagramAPIDataItem:
        if 'video_versions' in item:
            return InstagramAPIDataItem(
                InstagramAPIDataItem.CONTENT_TYPE_VIDEO,
                item['video_versions'][0]['url'])
        elif 'image_versions2' in item:
            return InstagramAPIDataItem(
                InstagramAPIDataItem.CONTENT_TYPE_IMAGE,
                item['image_versions2']['candidates'][0]['url'])
        else:
            raise PWarning(self.ERROR_MSG)

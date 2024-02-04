import json

import requests
from bs4 import BeautifulSoup

from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.utils import get_url_file_ext


class PinterestDataItem:
    CONTENT_TYPE_IMAGE = "image"
    CONTENT_TYPE_VIDEO = "video"
    CONTENT_TYPE_GIF = "gif"

    def __init__(self, content_type, download_url, caption=""):
        if content_type not in (self.CONTENT_TYPE_IMAGE, self.CONTENT_TYPE_VIDEO, self.CONTENT_TYPE_GIF):
            raise RuntimeError(
                f"content_type must be {self.CONTENT_TYPE_IMAGE} or {self.CONTENT_TYPE_VIDEO} or {self.CONTENT_TYPE_GIF}")

        self.content_type: str = content_type
        self.download_url: str = download_url
        self.caption: str = caption if caption else ""


class Pinterest:
    ERROR_MSG = "Ссылка на pinterest не является видео/фото/gif"

    def get_post_data(self, url) -> PinterestDataItem:
        content = requests.get(url).content
        bs4 = BeautifulSoup(content, 'html.parser')

        if bs4.find("script", {'data-test-id': 'video-snippet'}):
            return self._get_video(bs4)
        elif bs4.find("meta", {"name": "og:image"}):
            return self._get_photo(bs4)

        raise PWarning(self.ERROR_MSG)

    @staticmethod
    def _get_photo(bs4: BeautifulSoup) -> PinterestDataItem:
        try:
            image_data = json.loads(bs4.find("script", {'data-test-id': 'leaf-snippet'}).text)
            caption = image_data['headline']
            image_url = image_data['image']
        except Exception:
            caption = None
            image_url = bs4.find("meta", {"name": "og:image"}).attrs['content']

        ext = get_url_file_ext(image_url)
        content_type = PinterestDataItem.CONTENT_TYPE_GIF if ext in ['gif',
                                                                     'gifv'] else PinterestDataItem.CONTENT_TYPE_IMAGE
        return PinterestDataItem(content_type, image_url, caption)

    @staticmethod
    def _get_video(bs4: BeautifulSoup) -> PinterestDataItem:
        video_url = json.loads(bs4.find("script", {'data-test-id': 'video-snippet'}).text)['contentUrl']
        caption = bs4.find("meta", {"name": "og:title"}).attrs['content']
        return PinterestDataItem(PinterestDataItem.CONTENT_TYPE_VIDEO, video_url, caption)

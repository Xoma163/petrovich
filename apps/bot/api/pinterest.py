import json

import requests
from bs4 import BeautifulSoup

from apps.bot.utils.utils import get_url_file_ext


class Pinterest:
    CONTENT_TYPE_IMAGE = "image"
    CONTENT_TYPE_VIDEO = "video"
    CONTENT_TYPE_GIF = "gif"

    def get_post_data(self, url):
        content = requests.get(url).content
        bs4 = BeautifulSoup(content, 'html.parser')

        if bs4.find("script", {'data-test-id': 'video-snippet'}):
            return self._get_video(bs4)
        elif bs4.find("meta", {"name": "og:image"}):
            return self._get_photo(bs4)

        return None

    def _get_photo(self, bs4: BeautifulSoup):
        try:
            image_data = json.loads(bs4.find("script", {'data-test-id': 'leaf-snippet'}).text)
            title = image_data['headline']
            image_url = image_data['image']
        except Exception:
            title = None
            image_url = bs4.find("meta", {"name": "og:image"}).attrs['content']

        ext = get_url_file_ext(image_url)

        return {
            "download_url": image_url,
            "content_type": self.CONTENT_TYPE_GIF if ext in ['gif', 'gifv'] else self.CONTENT_TYPE_IMAGE,
            "title": title,
            "filename": f"{title.replace(' ', '_')}.{ext}"
        }

    def _get_video(self, bs4: BeautifulSoup) -> dict:
        video_url = json.loads(bs4.find("script", {'data-test-id': 'video-snippet'}).text)['contentUrl']
        ext = get_url_file_ext(video_url)
        title = bs4.find("meta", {"name": "og:title"}).attrs['content']
        return {
            "download_url": video_url,
            "content_type": self.CONTENT_TYPE_VIDEO,
            "title": title,
            "filename": f"{title.replace(' ', '_')}.{ext}"
        }

import json

import requests
from bs4 import BeautifulSoup

from apps.shared.exceptions import PWarning
from apps.shared.utils.utils import get_url_file_ext


class PinterestDataItem:
    CONTENT_TYPE_IMAGE = "image"
    CONTENT_TYPE_VIDEO = "video"
    CONTENT_TYPE_GIF = "gif"

    def __init__(self, content_type, download_url, caption=""):
        if content_type not in (self.CONTENT_TYPE_IMAGE, self.CONTENT_TYPE_VIDEO, self.CONTENT_TYPE_GIF):
            raise RuntimeError(
                f"content_type must be {self.CONTENT_TYPE_IMAGE} or {self.CONTENT_TYPE_VIDEO} or {self.CONTENT_TYPE_GIF}"
            )

        self.content_type: str = content_type
        self.download_url: str = download_url
        self.caption: str = caption if caption else ""


class Pinterest:
    ERROR_MSG = "Не удалось получить фото, видео или GIF из Pinterest. Проверьте ссылку на публикацию"

    def get_post_data(self, url) -> PinterestDataItem:
        content = requests.get(url).content
        bs4 = BeautifulSoup(content, "html.parser")

        if bs4.find("script", {"data-test-id": "video-snippet"}):
            return self._get_video(bs4)
        elif bs4.find("meta", {"name": "og:image"}):
            return self._get_photo(bs4)

        raise PWarning(self.ERROR_MSG)

    @staticmethod
    def _get_photo(bs4: BeautifulSoup) -> PinterestDataItem:
        caption = None
        image_url = None
        snippet = bs4.find("script", {"data-test-id": "leaf-snippet"})
        if snippet is not None:
            try:
                image_data = json.loads(snippet.text)
                caption = image_data["headline"]
                image_url = image_data["image"]
            except (json.JSONDecodeError, KeyError, TypeError):
                caption = None
        if not isinstance(image_url, str) or not image_url:
            image = bs4.find("meta", {"name": "og:image"})
            image_url = image.get("content") if image is not None else None
        if not image_url:
            raise PWarning(Pinterest.ERROR_MSG)

        ext = get_url_file_ext(image_url)
        content_type = (
            PinterestDataItem.CONTENT_TYPE_GIF if ext in ["gif", "gifv"] else PinterestDataItem.CONTENT_TYPE_IMAGE
        )
        return PinterestDataItem(content_type, image_url, caption)

    @staticmethod
    def _get_video(bs4: BeautifulSoup) -> PinterestDataItem:
        snippet = bs4.find("script", {"data-test-id": "video-snippet"})
        if snippet is None:
            raise PWarning(Pinterest.ERROR_MSG)
        try:
            video_url = json.loads(snippet.text)["contentUrl"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise PWarning(Pinterest.ERROR_MSG) from exc
        if not isinstance(video_url, str) or not video_url:
            raise PWarning(Pinterest.ERROR_MSG)
        title = bs4.find("meta", {"name": "og:title"})
        caption = title.get("content", "") if title is not None else ""
        return PinterestDataItem(PinterestDataItem.CONTENT_TYPE_VIDEO, video_url, caption)

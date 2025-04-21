import math
import re
import string
from urllib.parse import urlparse

from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.proxy import get_proxies


class TwitterAPIResponseItem:
    CONTENT_TYPE_IMAGE = 'image'
    CONTENT_TYPE_VIDEO = 'video'

    def __init__(self, content_type, download_url):
        if content_type not in (self.CONTENT_TYPE_IMAGE, self.CONTENT_TYPE_VIDEO):
            raise RuntimeError(f"content_type must be {self.CONTENT_TYPE_IMAGE} or {self.CONTENT_TYPE_VIDEO}")
        self.content_type = content_type
        self.download_url = download_url


class TwitterAPIResponse:
    def __init__(self):
        self.items: list[TwitterAPIResponseItem] = []
        self.caption: str = ""

    def add_item(self, item):
        self.items.append(item)


class Twitter(API):
    URL_TWEET_INFO = "https://cdn.syndication.twimg.com/tweet-result"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_post_data(self, url) -> TwitterAPIResponse:
        tweet_id = urlparse(url).path.strip('/').split('/')[-1]
        token = self._get_token(tweet_id)
        post_data = self.requests.get(
            self.URL_TWEET_INFO,
            params={'id': tweet_id, 'token': token},
            proxies=get_proxies()
        ).json()

        if not post_data:
            raise PWarning("Ошибка. В посте нет данных. Заведите ишу, плиз, гляну чё там")

        return self._get_text_and_attachments(post_data)

    def _get_text_and_attachments(self, post_data: dict) -> TwitterAPIResponse:
        finish_text_pos = self._get_finish_text_pos(post_data)

        text = post_data['text']
        if finish_text_pos:
            text = post_data['text'][:finish_text_pos]

        response = TwitterAPIResponse()
        response.caption = text

        media_data = post_data.get('mediaDetails')

        if not media_data:
            return response

        for entity in media_data:
            if entity['type'] == 'video':
                video = self._get_video(entity['video_info']['variants'])
                response.add_item(TwitterAPIResponseItem(TwitterAPIResponseItem.CONTENT_TYPE_VIDEO, video))
            elif entity['type'] == 'photo':
                photo = entity['media_url_https']
                response.add_item(TwitterAPIResponseItem(TwitterAPIResponseItem.CONTENT_TYPE_IMAGE, photo))
        return response

    @staticmethod
    def _get_finish_text_pos(post_data: dict) -> int | None:
        try:
            return post_data['entities']['media'][0]['indices'][0]
        except (KeyError, IndexError):
            pass

        try:
            return post_data['display_text_range'][1]
        except (KeyError, IndexError):
            pass

        return None

    @staticmethod
    def _get_video(video_info: list) -> str:
        videos = filter(lambda x: x.get('bitrate') is not None and x['content_type'] == 'video/mp4', video_info)
        best_video = sorted(videos, key=lambda x: x['bitrate'], reverse=True)[0]['url']
        return best_video

    def _get_token(self, _id):
        number = float(_id) / 1e15
        multiplied = number * math.pi
        base36 = self._to_base36(multiplied)
        result = re.sub(r'(0+|\.)', '', base36)
        return result

    @staticmethod
    def _to_base36(num):
        num = abs(int(num))
        if num == 0:
            return '0'
        result = ''
        chars = string.digits + string.ascii_lowercase
        while num:
            num, rem = divmod(num, 36)
            result = chars[rem] + result

        sign = '-' if num < 0 else ''
        return sign + result

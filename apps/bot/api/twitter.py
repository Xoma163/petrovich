import re
import time
from urllib.parse import urlparse

from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PWarning
from petrovich.settings import env


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
    _HOST = "twitter154.p.rapidapi.com"
    HEADERS = {
        "X-RapidAPI-Host": _HOST,
        "X-RapidAPI-Key": env.str("RAPID_API_KEY"),
    }
    URL_TWEET_INFO = f"https://{_HOST}/tweet/details"
    URL_TWEET_REPLIES = f"https://{_HOST}/tweet/replies"

    def __init__(self):
        super().__init__()

        self.requests.headers = self.HEADERS

    def get_post_data(self, url, with_threads=False) -> TwitterAPIResponse:
        tweet_id = urlparse(url).path.strip('/').split('/')[-1]
        r = self.requests.get(self.URL_TWEET_INFO, params={'tweet_id': tweet_id}).json()
        if r.get('detail') == 'Error while parsing tweet':
            raise PWarning("Ошибка на стороне API")

        if with_threads:
            try:
                return self._get_post_with_replies(r)
            except RuntimeError:
                return self._get_text_and_attachments(r)
        else:
            return self._get_text_and_attachments(r)

    def _get_text_and_attachments(self, tweet_data) -> TwitterAPIResponse:
        text = self._get_text_without_tco_links(tweet_data.get('text', ""))
        response = TwitterAPIResponse()
        response.caption = text

        if not tweet_data['extended_entities']:
            return response

        for entity in tweet_data['extended_entities']['media']:
            if entity['type'] == 'video':
                video = self._get_video(entity['video_info']['variants'])
                response.add_item(TwitterAPIResponseItem(TwitterAPIResponseItem.CONTENT_TYPE_VIDEO, video))
            elif entity['type'] == 'photo':
                photo = entity['media_url_https']
                response.add_item(TwitterAPIResponseItem(TwitterAPIResponseItem.CONTENT_TYPE_IMAGE, photo))
        return response

    def _get_post_with_replies(self, tweet_data) -> TwitterAPIResponse:
        time.sleep(1)
        tweet_id = tweet_data["tweet_id"]
        user_id = tweet_data['user']['user_id']

        r = self.requests.get(self.URL_TWEET_REPLIES, params={'tweet_id': tweet_id}).json()
        replies = list(filter(lambda x: x['user']['user_id'] == user_id, r['replies']))

        replies_tweet_reply_id_dict = {x['in_reply_to_status_id']: x for x in replies}

        tweet_chain = [tweet_data]
        while tweet_id in replies_tweet_reply_id_dict:
            current_tweet = replies_tweet_reply_id_dict[tweet_id]
            tweet_chain.append(current_tweet)
            tweet_id = current_tweet['tweet_id']
        del replies_tweet_reply_id_dict

        if len(tweet_chain) == 1:
            raise RuntimeError

        texts = []
        items = []
        for tweet in tweet_chain:
            data = self._get_text_and_attachments(tweet)
            if data.caption:
                texts.append(data.caption)
            if data.items:
                items += data.items

        response = TwitterAPIResponse()
        response.caption = "\n\n".join(texts)
        response.items = items
        return response

    @staticmethod
    def _get_text_without_tco_links(text: str) -> str:
        p = re.compile(r"https:\/\/t.co\/.*")
        for item in reversed(list(p.finditer(text))):
            start_pos = item.start()
            end_pos = item.end()
            text = text[:start_pos] + text[end_pos:]
        return text

    @staticmethod
    def _get_video(video_info: list) -> str:
        videos = filter(lambda x: x.get('bitrate') is not None and x['content_type'] == 'video/mp4', video_info)
        best_video = sorted(videos, key=lambda x: x['bitrate'], reverse=True)[0]['url']
        return best_video

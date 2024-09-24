import re
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
    _HOST = "twitter-api47.p.rapidapi.com"
    HEADERS = {
        "X-RapidAPI-Host": _HOST,
        "X-RapidAPI-Key": env.str("RAPID_API_KEY"),
    }
    URL_TWEET_INFO = f"https://{_HOST}/v2/tweet/details"

    API_ERROR = 'Error while parsing tweet'
    TWITTER_ACCESS_ERROR = 'You’re unable to view this Post because this account owner limits who can view their Posts. Learn more'
    MONTHLY_QUOTA_ERROR = 'exceeded the MONTHLY quota'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.requests.headers = self.HEADERS

    def get_post_data(self, url, with_threads=False) -> TwitterAPIResponse:
        tweet_id = urlparse(url).path.strip('/').split('/')[-1]
        r = self.requests.get(self.URL_TWEET_INFO, params={'tweetId': tweet_id}).json()

        if error := r.get('detail') == self.API_ERROR:
            raise PWarning("Ошибка на стороне API")
        elif error == self.TWITTER_ACCESS_ERROR:
            raise PWarning("Пользователь ограничил круг лиц, которые могут видеть этот пост")
        if r.get('message') and self.MONTHLY_QUOTA_ERROR in r['message']:
            raise PWarning("Закончились запросы к API((")

        post_data = r.get('details', {}).get('legacy', {})
        threads = r.get('threadContent')

        if not post_data:
            raise PWarning("Ошибка. В посте нет данных. Заведите ишу, плиз, гляну чё там")

        if with_threads and threads:
            try:
                return self._get_post_with_replies(post_data, threads)
            except RuntimeError:
                return self._get_text_and_attachments(post_data)
        else:
            return self._get_text_and_attachments(post_data)

    def _get_text_and_attachments(self, post_data) -> TwitterAPIResponse:
        text = self._get_text_without_tco_links(post_data.get('full_text', ""))
        response = TwitterAPIResponse()
        response.caption = text

        if not post_data.get('extended_entities'):
            return response

        for entity in post_data['extended_entities']['media']:
            if entity['type'] == 'video':
                video = self._get_video(entity['video_info']['variants'])
                response.add_item(TwitterAPIResponseItem(TwitterAPIResponseItem.CONTENT_TYPE_VIDEO, video))
            elif entity['type'] == 'photo':
                photo = entity['media_url_https']
                response.add_item(TwitterAPIResponseItem(TwitterAPIResponseItem.CONTENT_TYPE_IMAGE, photo))
        return response

    def _get_post_with_replies(self, post_data: dict, threads: list) -> TwitterAPIResponse:
        tweet_id = post_data.get('id_str')
        user_id = post_data.get('user_id_str')

        threads = [x for x in threads if x[0]['legacy']['user_id_str'] == user_id][0]
        replies = list(filter(lambda x: x['legacy']['user_id_str'] == user_id, threads))

        replies_tweet_reply_id_dict = {x['legacy']['in_reply_to_status_id_str']: x for x in replies}

        tweet_chain = [post_data]
        while tweet_id in replies_tweet_reply_id_dict:
            current_tweet = replies_tweet_reply_id_dict[tweet_id]
            tweet_chain.append(current_tweet['legacy'])
            tweet_id = current_tweet['rest_id']
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

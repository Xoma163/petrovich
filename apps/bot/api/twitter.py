import re
import time
from urllib.parse import urlparse

from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PWarning
from petrovich.settings import env


class Twitter(API):
    CONTENT_TYPE_IMAGE = 'image'
    CONTENT_TYPE_VIDEO = 'video'
    CONTENT_TYPE_TEXT = 'text'

    _HOST = "twitter154.p.rapidapi.com"
    HEADERS = {
        "X-RapidAPI-Host": _HOST,
        "X-RapidAPI-Key": env.str("RAPID_API_KEY"),
    }
    URL_TWEET_INFO = f"https://{_HOST}/tweet/details"
    URL_TWEET_REPLIES = f"https://{_HOST}/tweet/replies"

    def get_post_data(self, url, with_threads=False):
        tweet_id = urlparse(url).path.strip('/').split('/')[-1]
        r = self.requests.get(self.URL_TWEET_INFO, headers=self.HEADERS, params={'tweet_id': tweet_id}).json()
        if r.get('detail') == 'Error while parsing tweet':
            raise PWarning("Ошибка на стороне API")

        if with_threads:
            try:
                return self._get_post_with_replies(r)
            except RuntimeError:
                return self._get_text_and_attachments(r)
        else:
            return self._get_text_and_attachments(r)

    def _get_text_and_attachments(self, tweet_data) -> dict:
        text = self._get_text_without_tco_links(tweet_data.get('text', ""))
        attachments = []
        if tweet_data.get('video_url'):
            video = self._get_video(tweet_data['video_url'])
            attachments = [{self.CONTENT_TYPE_VIDEO: video}]
        elif tweet_data.get('extended_entities') and tweet_data['extended_entities']['media'][0].get("video_info"):
            video = self._get_video(tweet_data['extended_entities']['media'][0].get("video_info", {}).get("variants"))
            attachments = [{self.CONTENT_TYPE_VIDEO: video}]
        elif tweet_data.get('media_url'):
            photos = self._get_photos(tweet_data['extended_entities']['media'])
            attachments = [{self.CONTENT_TYPE_IMAGE: x} for x in photos]
        return {'text': text, "attachments": attachments}

    def _get_post_with_replies(self, tweet_data) -> dict:
        time.sleep(1)
        tweet_id = tweet_data["tweet_id"]
        user_id = tweet_data['user']['user_id']

        r = self.requests.get(self.URL_TWEET_REPLIES, headers=self.HEADERS, params={'tweet_id': tweet_id}).json()
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
        attachments = []
        for tweet in tweet_chain:
            data = self._get_text_and_attachments(tweet)
            if data["text"]:
                texts.append(data["text"])
            if data["attachments"]:
                attachments += data["attachments"]
        return {
            'text': "\n\n".join(texts),
            'attachments': attachments
        }

    @staticmethod
    def _get_text_without_tco_links(text: str) -> str:
        p = re.compile(r"https:\/\/t.co\/.*")
        for item in reversed(list(p.finditer(text))):
            start_pos = item.start()
            end_pos = item.end()
            text = text[:start_pos] + text[end_pos:]
        return text

    @staticmethod
    def _get_photos(photo_info: dict) -> list:
        return [x['media_url_https'] for x in photo_info if x['type'] == 'photo']

    @staticmethod
    def _get_video(video_info: list) -> str:
        videos = filter(lambda x: x.get('bitrate') is not None and x['content_type'] == 'video/mp4', video_info)
        best_video = sorted(videos, key=lambda x: x['bitrate'], reverse=True)[0]['url']
        return best_video

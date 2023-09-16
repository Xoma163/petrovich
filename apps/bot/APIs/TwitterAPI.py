import logging
import re
import time
from urllib.parse import urlparse

import requests

from apps.bot.classes.consts.Exceptions import PWarning
from petrovich.settings import env

logger = logging.getLogger('bot')


class TwitterAPI:
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

    def __init__(self):
        self.content_type = None
        self.caption = ""
        self.with_replies = False

    def get_content_url(self, url):
        tweet_id = urlparse(url).path.strip('/').split('/')[-1]
        r = requests.get(self.URL_TWEET_INFO, headers=self.HEADERS, params={'tweet_id': tweet_id}).json()
        if r.get('detail') == 'Error while parsing tweet':
            raise PWarning("Ошибка на стороне API")
        logger.debug({"response": r})
        first_post_text, first_post_attachments = self.get_text_and_attachments(r)

        time.sleep(1)
        text_with_replies, attachments_in_replies = self.get_post_and_replies(first_post_text, first_post_attachments,
                                                                              tweet_id, r['user']['user_id'])
        if first_post_text != text_with_replies:
            self.with_replies = True

        self.caption = text_with_replies
        # self.caption = first_post_text
        # return first_post_attachments
        return attachments_in_replies

    def get_text_and_attachments(self, tweet_data) -> (str, list):
        text = self._get_text_without_tco_links(tweet_data.get('text', ""))
        attachments = []
        if tweet_data.get('video_url'):
            video = self._get_video(tweet_data['video_url'])
            attachments = [{self.CONTENT_TYPE_VIDEO: video}]
        elif tweet_data.get('extended_entities') and tweet_data['extended_entities']['media'][0].get("video_info"):
            video = self._get_video(tweet_data['extended_entities']['media'][0].get("video_info"))
            attachments = [{self.CONTENT_TYPE_VIDEO: video}]
        elif tweet_data.get('media_url'):
            photos = self._get_photos(tweet_data['media_url'])
            attachments = [{self.CONTENT_TYPE_IMAGE: x} for x in photos]
        return text, attachments

    def _get_text_without_tco_links(self, text):
        p = re.compile(r"https:\/\/t.co\/.*")  # markdown bold
        for item in reversed(list(p.finditer(text))):
            start_pos = item.start()
            end_pos = item.end()
            text = text[:start_pos] + text[end_pos:]
        return text

    @staticmethod
    def _get_photos(photo_info):
        return photo_info

    @staticmethod
    def _get_video(video_info):
        videos = filter(lambda x: x.get('bitrate') and x['content_type'] == 'video/mp4', video_info['variants'])
        best_video = sorted(videos, key=lambda x: x['bitrate'], reverse=True)[0]['url']
        return best_video

    def get_post_and_replies(self, tweet_text: str, tweet_attachments: list, tweet_id, user_id) -> (str, list):
        r = requests.get(self.URL_TWEET_REPLIES, headers=self.HEADERS, params={'tweet_id': tweet_id}).json()
        logger.debug({"response": r})
        replies = list(filter(lambda x: x['user']['user_id'] == user_id, r['replies']))

        replies_tweet_reply_id_dict = {x['in_reply_to_status_id']: x for x in replies}

        tweet_chain = []
        while tweet_id in replies_tweet_reply_id_dict:
            current_tweet = replies_tweet_reply_id_dict[tweet_id]
            tweet_chain.append(current_tweet)
            tweet_id = current_tweet['tweet_id']
        del replies_tweet_reply_id_dict

        texts = [tweet_text]
        attachments = tweet_attachments
        for tweet in tweet_chain:
            _text, _attachments = self.get_text_and_attachments(tweet)
            if _text:
                texts.append(_text)
            if _attachments:
                attachments += _attachments
        return "\n\n".join(texts), attachments

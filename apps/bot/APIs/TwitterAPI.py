from urllib.parse import urlparse

import requests

from apps.bot.classes.consts.Exceptions import PWarning
from petrovich.settings import env


class TwitterAPI:
    CONTENT_TYPE_IMAGE = 'image'
    CONTENT_TYPE_VIDEO = 'video'
    CONTENT_TYPE_TEXT = 'text'

    _HOST = "twitter154.p.rapidapi.com"
    HEADERS = {
        "X-RapidAPI-Host": _HOST,
        "X-RapidAPI-Key": env.str("RAPID_API_KEY"),
    }
    URL = f"https://{_HOST}/tweet/details"

    def __init__(self):
        self.content_type = None
        self.caption = ""

    def get_content_url(self, url):
        tweet_id = urlparse(url).path.strip('/').split('/')[-1]
        r = requests.get(f"{self.URL}", headers=self.HEADERS, params={'tweet_id': tweet_id}).json()
        if r.get('video_url'):
            videos = filter(lambda x: x.get('bitrate') and x['content_type'] == 'video/mp4', r['video_url'])
            best_video = sorted(videos, key=lambda x: x['bitrate'], reverse=True)[0]['url']
            self.caption = r['text'].rsplit(' ', 1)[0]
            self.content_type = self.CONTENT_TYPE_VIDEO
            return best_video
        elif r.get('media_url'):
            self.caption = r['text'].rsplit(' ', 1)[0]
            self.content_type = self.CONTENT_TYPE_IMAGE
            return r['media_url']
        elif 'text' in r:
            self.caption = r['text'].rsplit(' ', 1)[0]
            self.content_type = self.CONTENT_TYPE_TEXT
        else:
            raise PWarning("Ссылка на твит не является видео/фото/текстом")

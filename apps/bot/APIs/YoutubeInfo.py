from datetime import datetime

import requests
from bs4 import BeautifulSoup

from apps.bot.classes.consts.Exceptions import PWarning


class YoutubeInfo:
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    def get_youtube_last_video(self):
        response = requests.get(self.url)
        if response.status_code != 200:
            raise PWarning("Не нашёл такого канала")
        bsop = BeautifulSoup(response.content, 'html.parser')
        last_video = bsop.find_all('entry')[0]
        youtube_info = {
            'title': bsop.find('title').text,
            'last_video': {
                'title': last_video.find('title').text,
                'link': last_video.find('link').attrs['href'],
                'date': datetime.strptime(last_video.find('published').text, '%Y-%m-%dT%H:%M:%S%z'),
            }
        }
        return youtube_info

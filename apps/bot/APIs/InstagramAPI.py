import json

import requests
from bs4 import BeautifulSoup

from apps.bot.classes.consts.Exceptions import PWarning


class InstagramAPI:
    CONTENT_TYPE_IMAGE = 'image'
    CONTENT_TYPE_VIDEO = 'video'
    CONTENT_TYPE_REEL = 'reel'

    def __init__(self):
        self.content_type = None

    def get_content_url(self, url):
        r = requests.get(url)
        bs4 = BeautifulSoup(r.content, 'html.parser')
        if bs4.find("html", {'class': "not-logged-in"}):
            raise PWarning("Требуется логин для скачивания")
        if 'reel' in url:
            content_type = self.CONTENT_TYPE_REEL
        else:
            try:
                content_type = bs4.find('meta', attrs={'name': 'medium'}).attrs['content']
            except Exception:
                raise PWarning("Ссылка на инстаграмм не является видео/фото")

        if content_type == self.CONTENT_TYPE_IMAGE:
            photo_url = bs4.find('meta', attrs={'property': 'og:image'}).attrs['content']
            self.content_type = self.CONTENT_TYPE_IMAGE
            return photo_url
        elif content_type == 'video':
            try:
                video_url = bs4.find('meta', attrs={'property': 'og:video'}).attrs['content']
            except:
                raise PWarning("Не получилось распарсить видео с инстаграма")
            self.content_type = self.CONTENT_TYPE_VIDEO
            return video_url
        elif content_type == 'reel':
            shared_data_text = "window._sharedData = "
            script_text = ";</script>"
            pos_start = r.text.find(shared_data_text) + len(shared_data_text)
            pos_end = r.text.find(script_text, pos_start)
            reel_data = json.loads(r.text[pos_start:pos_end])
            entry_data = reel_data['entry_data']
            if 'LoginAndSignupPage' in entry_data:
                raise PWarning("Этот reel скачать не получится, требуется авторизация :(")
            video_url = entry_data['PostPage'][0]['graphql']['shortcode_media']['video_url']
            self.content_type = self.CONTENT_TYPE_REEL
            return video_url
        else:
            raise PWarning("Ссылка на инстаграмм не является видео/фото")

import json

import requests
from bs4 import BeautifulSoup


class PinterestAPI:
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"

    def __init__(self, url):
        self.url = url
        self.title = None
        self.type = None

    def get_attachment(self):
        content = requests.get(self.url).content
        bs4 = BeautifulSoup(content, 'html.parser')
        # meta = bs4.find_all("meta")
        self.title = bs4.find("meta", {"name": "og:title"}).attrs['content']

        if bs4.find("script", {'data-test-id': 'video-snippet'}):
            return self.get_video(bs4)
        elif bs4.find("meta", {"name": "og:image"}):
            return self.get_photo(bs4)

        return None

    def get_photo(self, bs4):
        self.type = self.IMAGE
        try:
            image = json.loads(bs4.find("script", {'data-test-id': 'leaf-snippet'}).text)
            self.title = image['headline']
            image_url = image['image']
            if image_url.endswith('.gif') or image_url.endswith('.gifv'):
                self.type = self.GIF
        except:
            self.title = None
            image_url = bs4.find("meta", {"name": "og:image"}).attrs['content']
        return image_url

    def get_video(self, bs4):
        self.type = self.VIDEO
        return json.loads(bs4.find("script", {'data-test-id': 'video-snippet'}).text)['contentUrl']

    @property
    def is_video(self):
        return self.type == self.VIDEO

    @property
    def is_image(self):
        return self.type == self.IMAGE

    @property
    def is_gif(self):
        return self.type == self.GIF

import requests

from apps.bot.classes.consts.Exceptions import PWarning
from petrovich.settings import env


class FacebookVideoAPI:
    _HOST = "facebook-reel-and-video-downloader.p.rapidapi.com"
    HEADERS = {
        "X-RapidAPI-Host": _HOST,
        "X-RapidAPI-Key": env.str("RAPID_API_KEY"),
    }
    URL = f"https://{_HOST}/app/main.php"

    def __init__(self):
        self.caption = ""

    def get_content_url(self, url):
        response = requests.get(self.URL, headers=self.HEADERS, params={"url": url}).json()
        if response.get('title'):
            self.caption = response['title']

        video_url = None
        if response['links']:
            video_url = response['links']['Download High Quality'] or response['links']['Download Low Quality']
        if not video_url:
            raise PWarning("Ссылка на инстаграмм не является видео/фото")
        return video_url

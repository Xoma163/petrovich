import requests
from bs4 import BeautifulSoup

from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import get_url_file_ext


class PikabuAPI:
    def __init__(self):
        self.title = None
        self.filename = None

    def get_video_url_from_post(self, url):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        r = requests.get(url, headers=headers)
        bs4 = BeautifulSoup(r.content, 'html.parser')
        player = bs4.select_one(".page-story .page-story__story .player")
        if not player:
            raise PWarning("Не нашёл видео в этом посте")
        self.title = bs4.find('meta', attrs={'property': 'og:title'}).attrs['content']
        webm = player.attrs['data-webm']
        ext = get_url_file_ext(webm)
        self.filename = f"{self.title.replace(' ', '.')}.{ext}"
        return webm

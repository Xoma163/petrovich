import requests
from bs4 import BeautifulSoup

from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.utils import get_url_file_ext


class Pikabu:
    HEADERS = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    def get_video_data(self, url) -> dict:
        r = requests.get(url, headers=self.HEADERS)
        bs4 = BeautifulSoup(r.content, 'html.parser')
        player = bs4.select_one(".page-story .page-story__story .player")
        if not player:
            raise PWarning("Не нашёл видео в этом посте")

        video_url = player.attrs['data-webm']
        ext = get_url_file_ext(video_url)
        title = bs4.find('meta', attrs={'property': 'og:title'}).attrs['content']
        return {
            "download_url": video_url,
            "filename": f"{title.replace(' ', '.')}.{ext}",
            "title": title
        }

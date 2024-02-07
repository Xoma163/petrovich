import requests
from bs4 import BeautifulSoup

from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.utils import get_url_file_ext, get_default_headers


class Pikabu:
    HEADERS = get_default_headers()

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

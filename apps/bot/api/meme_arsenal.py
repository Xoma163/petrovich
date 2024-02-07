from typing import List

from apps.bot.api.handler import API
from apps.bot.utils.utils import get_default_headers


class MemeArsenal(API):
    URL = " https://api.meme-arsenal.com/api/templates-share"
    HEADERS = get_default_headers()

    def get_memes(self, text, items_on_page=5) -> List[dict]:
        params = {
            'sort': 'popular',
            'items_on_page': items_on_page,
            'lang': 'ru',
            'query': text,
        }
        r = self.requests.get(self.URL, params, headers=self.HEADERS).json()

        return [{'title': x['title'], 'url': x['url']} for x in r['data']]

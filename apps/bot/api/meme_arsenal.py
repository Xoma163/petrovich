from typing import List

from apps.bot.api.handler import API


class MemeArsenal(API):
    URL = " https://api.meme-arsenal.com/api/templates-share"
    HEADERS = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    def get_memes(self, text, items_on_page=5) -> List[dict]:
        params = {
            'sort': 'popular',
            'items_on_page': items_on_page,
            'lang': 'ru',
            'query': text,
        }
        r = self.requests.get(self.URL, params, headers=self.HEADERS).json()

        return [{'title': x['title'], 'url': x['url']} for x in r['data']]

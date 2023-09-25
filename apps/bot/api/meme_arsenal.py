import logging
from typing import List

import requests

logger = logging.getLogger('responses')


class MemeArsenal:
    URL = " https://api.meme-arsenal.com/api/templates-share"

    def get_memes(self, text, items_on_page=5) -> List[dict]:
        r = requests.get(self.URL, {
            'sort': 'popular',
            'items_on_page': items_on_page,
            'lang': 'ru',
            'query': text,
        }).json()
        logger.debug({"response": r})

        return [{'title': x['title'], 'url': x['url']} for x in r['data']]

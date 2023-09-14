import logging

import requests

logger = logging.getLogger('bot')


class MemeArsenalAPI:
    URL = " https://api.meme-arsenal.com/api/templates-share"

    def __init__(self):
        pass

    def get_memes(self, text, items_on_page=5):
        r = requests.get(self.URL, {
            'sort': 'popular',
            'items_on_page': items_on_page,
            'lang': 'ru',
            'query': text,
        }).json()
        logger.debug({"response": r})

        return [{'title': x['title'], 'url': x['url']} for x in r['data']]

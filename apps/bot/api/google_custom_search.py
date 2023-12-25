from typing import List

from apps.bot.api.handler import API
from petrovich.settings import env


class GoogleCustomSearch(API):
    URL = "https://customsearch.googleapis.com/customsearch/v1?"

    def get_images_urls(self, query) -> List[str]:
        querystring = {
            "key": env.str("GOOGLE_API_KEY"),
            "cx": env.str("GOOGLE_SEARCH_ENGINE_ID"),
            "searchType": "image",
            "safe": "active",
            "q": query
        }

        r = self.requests.get(self.URL, params=querystring).json()

        images_urls = []
        if 'items' in r:
            images_urls = [x['link'] for x in r['items']]
        return images_urls

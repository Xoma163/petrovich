import requests

from petrovich.settings import env


class GoogleCustomSearchAPI:
    URL = "https://customsearch.googleapis.com/customsearch/v1?"

    def get_images_urls(self, query):
        querystring = {
            "key": env.str("GOOGLE_API_KEY"),
            "cx": env.str("GOOGLE_SEARCH_ENGINE_ID"),
            "searchType": "image",
            "safe": "active",
            "q": query
        }

        response = requests.get(self.URL, params=querystring).json()
        images_urls = []
        if 'items' in response:
            images_urls = [x['link'] for x in response['items']]
        return images_urls

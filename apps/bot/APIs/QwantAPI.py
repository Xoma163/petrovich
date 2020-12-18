import requests


class QwantAPI:
    def __init__(self, ):
        self.url = "https://api.qwant.com/api/search/images"

    def get_urls(self, query):
        r = requests.get(
            self.url,
            params={
                'count': 10,
                'q': query,
                't': 'images',
                'safesearch': 1,
                'locale': 'ru_RU',
                'uiv': 4
            },
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
            }
        )
        if r.status_code == 429:
            raise RuntimeWarning("Сегодняшний лимит исчерпан")
        r_json = r.json()
        if r_json['status'] == 'error':
            raise RuntimeError("Ошибка API")
        response = r.json().get('data').get('result').get('items')
        urls = [r.get('media') for r in response]
        return urls

import requests


class TgRequests:
    API_TELEGRAM_URL = 'api.telegram.org'

    def __init__(self, token):
        self.token = token

    def get(self, method_name, params=None, **kwargs):
        url = f'https://{self.API_TELEGRAM_URL}/bot{self.token}/{method_name}'
        return requests.get(url, params, **kwargs)

    def post(self, method_name, params=None, **kwargs):
        url = f'https://{self.API_TELEGRAM_URL}/bot{self.token}/{method_name}'
        return requests.post(url, params, **kwargs)


class TgRequestLocal:
    API_TELEGRAM_URL = '192.168.1.10:10010'

    def __init__(self, token):
        self.token = token

    def get(self, method_name, params=None, **kwargs):
        url = f'http://{self.API_TELEGRAM_URL}/bot{self.token}/{method_name}'
        return requests.get(url, params, **kwargs)

    def post(self, method_name, params=None, **kwargs):
        url = f'http://{self.API_TELEGRAM_URL}/bot{self.token}/{method_name}'
        return requests.post(url, params, **kwargs)

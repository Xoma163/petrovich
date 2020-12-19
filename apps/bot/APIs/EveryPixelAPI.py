import requests

from apps.bot.classes.Exceptions import PWarning, PError
from petrovich.settings import env


class EveryPixelAPI:
    def __init__(self):
        self.image_quality_URL = 'https://api.everypixel.com/v1/quality_ugc'
        self.image_faces_URL = 'https://api.everypixel.com/v1/faces'
        self.CLIENT_ID = env.str("EVERYPIXEL_CLIENT_ID")
        self.CLIENT_SECRET = env.str("EVERYPIXEL_CLIENT_SECRET")

    def get_image_quality_by_url(self, url):
        params = {
            'url': url
        }
        return requests.get(self.image_quality_URL,
                            params,
                            auth=(self.CLIENT_ID, self.CLIENT_SECRET)).json()

    def get_image_quality_by_file(self, file):
        data = {'data': file}
        return requests.post(self.image_quality_URL,
                             files=data,
                             auth=(self.CLIENT_ID, self.CLIENT_SECRET)).json()

    def get_image_quality(self, url_or_bytes):
        if isinstance(url_or_bytes, str):
            response = self.get_image_quality_by_url(url_or_bytes)
        else:
            response = self.get_image_quality_by_file(url_or_bytes)

        if response['status'] != 'ok':
            raise PError("Ошибка")
        return f"{round(response['quality']['score'] * 100, 2)}%"

    def get_faces_on_photo_by_url(self, url):
        params = {'url': url}
        return requests.get(self.image_faces_URL,
                            params=params,
                            auth=(self.CLIENT_ID, self.CLIENT_SECRET)).json()

    def get_faces_on_photo_by_file(self, file):
        data = {
            'data': file
        }
        return requests.post(self.image_faces_URL,
                             files=data,
                             auth=(self.CLIENT_ID, self.CLIENT_SECRET)).json()

    def get_faces_on_photo(self, url_or_bytes):
        if isinstance(url_or_bytes, str):
            response = self.get_faces_on_photo_by_url(url_or_bytes)
        else:
            response = self.get_faces_on_photo_by_file(url_or_bytes)

        if response['status'] == 'error':
            if response['message'] == 'ratelimit exceeded 100 requests per 86400 seconds':
                raise PWarning("Сегодняшний лимит исчерпан")
            raise PError("Ошибка получения возраста на изображении")
        if response['status'] != "ok":
            raise PError("Ошибка. Статус не ок((")
        return response['faces']

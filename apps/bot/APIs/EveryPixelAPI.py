import requests

from petrovich.settings import env


class EveryPixelAPI:
    def __init__(self, image_url):
        self.image_quality_URL = 'https://api.everypixel.com/v1/quality_ugc'
        self.image_faces_URL = 'https://api.everypixel.com/v1/faces'
        self.CLIENT_ID = env.str("EVERYPIXEL_CLIENT_ID")
        self.CLIENT_SECRET = env.str("EVERYPIXEL_CLIENT_SECRET")

        self.image_URL = image_url

    def get_image_quality(self):
        params = {
            'url': self.image_URL
        }
        response = requests.get(self.image_quality_URL,
                                params,
                                auth=(self.CLIENT_ID, self.CLIENT_SECRET)).json()

        if response['status'] == 'ok':
            return f"{round(response['quality']['score'] * 100, 2)}%"
        else:
            print(response)
            raise RuntimeError("Ошибка")

    def get_faces_on_photo(self):
        params = {'url': self.image_URL}
        response = requests.get(self.image_faces_URL,
                                params=params,
                                auth=(self.CLIENT_ID, self.CLIENT_SECRET)).json()
        if response['status'] == 'error':
            if response['message'] == 'ratelimit exceeded 100 requests per 86400 seconds':
                raise RuntimeError("Сегодняшний лимит исчерпан")
            raise RuntimeError("Ошибка получения возраста на изображении")
        if response['status'] != "ok":
            raise RuntimeError("Ошибка. Статус не ок((")
        return response['faces']

from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PWarning, PError
from petrovich.settings import env


class EveryPixel(API):
    IMAGE_QUALITY_URL = 'https://api.everypixel.com/v1/quality_ugc'
    IMAGE_FACES_URL = 'https://api.everypixel.com/v1/faces'
    CLIENT_ID = env.str("EVERYPIXEL_CLIENT_ID")
    CLIENT_SECRET = env.str("EVERYPIXEL_CLIENT_SECRET")

    RATE_LIMIT_ERROR = 'ratelimit exceeded 100 requests per 86400 seconds'

    def get_image_quality_by_file(self, file) -> dict:
        data = {'data': file}
        r = self.requests.post(self.IMAGE_QUALITY_URL, files=data, auth=(self.CLIENT_ID, self.CLIENT_SECRET)).json()
        return r

    def get_image_quality(self, _bytes) -> str:
        r = self.get_image_quality_by_file(_bytes)

        if r['status'] != 'ok':
            raise PError("Ошибка")
        return f"{round(r['quality']['score'] * 100, 2)}%"

    def get_faces_on_photo_by_file(self, file) -> dict:
        data = {
            'data': file
        }
        r = self.requests.post(self.IMAGE_FACES_URL, files=data, auth=(self.CLIENT_ID, self.CLIENT_SECRET)).json()
        return r

    def get_faces_on_photo(self, _bytes) -> dict:
        r = self.get_faces_on_photo_by_file(_bytes)

        if r['status'] == 'error':
            if r['message'] == self.RATE_LIMIT_ERROR:
                raise PWarning("Сегодняшний лимит исчерпан")
            raise PError("Ошибка получения возраста на изображении")
        if r['status'] != "ok":
            raise PError("Ошибка. Статус не ок((")
        return r['faces']

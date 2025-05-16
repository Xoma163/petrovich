from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PWarning
from petrovich.settings import env


class Imgur(API):
    ACCESS_TOKEN = env.str("IMGUR_ACCESS_TOKEN")

    HOST = "https://api.imgur.com"
    URL_UPLOAD = f"{HOST}/3/upload"

    HEADERS = {"Authorization": f"Client-ID {ACCESS_TOKEN}"}

    def upload_image(self, image: bytes) -> str:
        files = {
            "image": image
        }
        r = self.requests.post(self.URL_UPLOAD, files=files, headers=self.HEADERS).json()
        try:
            return r['data']['link']
        except KeyError:
            raise PWarning("Ошибка на стороне Imgur")

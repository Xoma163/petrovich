import logging

import requests

from petrovich.settings import env

logger = logging.getLogger('bot')


class ImgurAPI:
    # CLIENT_ID = env.str("IMGUR_CLIENT_ID")
    # CLIENT_SECRET = env.str("IMGUR_CLIENT_SECRET")
    ACCESS_TOKEN = env.str("IMGUR_ACCESS_TOKEN")
    # REFRESH_TOKEN = env.str("IMGUR_REFRESH_TOKEN")

    HOST = "https://api.imgur.com"
    URL_UPLOAD = f"{HOST}/3/upload"

    HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    def __init__(self):
        pass

    def upload_image(self, image: bytes) -> str:
        files = {
            "image": image
        }
        r = requests.post(self.URL_UPLOAD, files=files, headers=self.HEADERS).json()
        logger.debug({"response": r})

        return r['data']['link']

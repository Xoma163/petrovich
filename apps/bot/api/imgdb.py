from apps.bot.api.handler import API
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from petrovich.settings import env


class ImgdbAPI(API):
    API_KEY = env.str("IMGDB_API_KEY")

    BASE_URL = "https://api.imgbb.com"
    IMAGE_UPLOAD_URL = f"{BASE_URL}/1/upload"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def upload_image(self, image: PhotoAttachment, expire: int | None = None):
        content = image.download_content()
        params = {'key': self.API_KEY}
        if expire is not None:
            expire = max(expire, 60)
            expire = min(expire, 15552000)
            params['expiration'] = expire
        files = {
            'image': (image.file_name_full, content)
        }
        response = self.requests.post(self.IMAGE_UPLOAD_URL, params=params, files=files)
        return response.json()['data']['image']['url']

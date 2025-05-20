from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.proxy import get_proxies
from petrovich.settings import env


class InstagramAPIDataItem:
    CONTENT_TYPE_IMAGE = 'image'
    CONTENT_TYPE_VIDEO = 'video'

    def __init__(self, content_type, download_url):
        if content_type not in (self.CONTENT_TYPE_IMAGE, self.CONTENT_TYPE_VIDEO):
            raise RuntimeError(f"content_type must be {self.CONTENT_TYPE_IMAGE} or {self.CONTENT_TYPE_VIDEO}")

        self.content_type = content_type
        self.download_url = download_url


class InstagramAPIData:
    def __init__(self):
        self.items: list[InstagramAPIDataItem] = []
        self.caption: str = ""

    def add_item(self, item: InstagramAPIDataItem):
        self.items.append(item)


class Instagram(API):
    RAPID_API_KEY = env.str("RAPID_API_KEY")

    HOST = "instagram-scraper-api2.p.rapidapi.com"
    URL = f'https://{HOST}/v1/post_info'
    HEADERS = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": HOST
    }

    LOCATION_BANNED_ERROR = "Sorry, we are unable to provide RapidAPI services to your location"


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.requests.headers = self.HEADERS

    def get_data(self, instagram_link) -> InstagramAPIData:
        params = {"code_or_id_or_url": instagram_link}
        r = self.requests.get(self.URL, params=params, proxies=get_proxies()).json()
        if error_message := r.get("messages"):
            if error_message.startswith(self.LOCATION_BANNED_ERROR):
                raise PWarning("API забанили. Я в курсе проблемы, постараюсь решить как можно скорее")
        if not r.get('data'):
            raise PWarning("Ошибка API")
        return self._parse_response(r['data'])

    @staticmethod
    def _parse_response(item) -> InstagramAPIData:
        data = InstagramAPIData()

        # caption
        caption_block = item.get('caption') if item else None
        data.caption = caption_block.get('text') if caption_block else None

        if carousel := item.get('carousel_media'):
            for carousel_item in carousel:
                if video_url := carousel_item.get('video_url'):
                    data.add_item(InstagramAPIDataItem(InstagramAPIDataItem.CONTENT_TYPE_VIDEO, video_url))
                elif image_versions := carousel_item.get('image_versions'):
                    image_url = image_versions['items'][0]['url']
                    data.add_item(InstagramAPIDataItem(InstagramAPIDataItem.CONTENT_TYPE_IMAGE, image_url))
        elif video_url := item.get('video_url'):
            data.add_item(InstagramAPIDataItem(InstagramAPIDataItem.CONTENT_TYPE_VIDEO, video_url))
        elif display_url := item.get('display_url'):
            data.add_item(InstagramAPIDataItem(InstagramAPIDataItem.CONTENT_TYPE_IMAGE, display_url))
        elif image_versions := item.get('image_versions'):
            image_url = image_versions['items'][0]['url']
            data.add_item(InstagramAPIDataItem(InstagramAPIDataItem.CONTENT_TYPE_IMAGE, image_url))

        return data

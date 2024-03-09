from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PWarning
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

    HOST = "instagram-post-reels-stories-downloader.p.rapidapi.com"
    URL = f'https://{HOST}/instagram/'
    HEADERS = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": HOST
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.requests.headers = self.HEADERS

    def get_data(self, instagram_link) -> InstagramAPIData:
        params = {"url": instagram_link}
        r = self.requests.get(self.URL, params=params).json()
        if not r.get('result'):
            raise PWarning("Ошибка API")
        return self._parse_response(r['result'])

    def _parse_response(self, response) -> InstagramAPIData:
        data = InstagramAPIData()
        # data.caption = response[0]['title']
        for item in response:
            print(item['type'])
            if item['type'] == "video/mp4":
                content_type = InstagramAPIDataItem.CONTENT_TYPE_VIDEO
            else:
                content_type = InstagramAPIDataItem.CONTENT_TYPE_IMAGE

            data_item = InstagramAPIDataItem(
                content_type,
                item['url']
            )
            data.add_item(data_item)

        return data

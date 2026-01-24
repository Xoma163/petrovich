import json

from bs4 import BeautifulSoup
from selenium.common import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from apps.bot.utils.decorators import retry
from apps.bot.utils.web_driver import get_web_driver, get_web_driver_headers
from apps.connectors.parsers.media_command.data import VideoData
from apps.shared.exceptions import PWarning


class TikTok:
    AGE_RESTRICTION_MESSAGE = r'This post may not be comfortable for some audiences. Log in to make the most of your experience.'

    def __init__(self):
        super().__init__()

        self.errors = {
            10231: "Не могу скачать контент. Недоступно в нашей стране"
        }

    @retry(times=5, exceptions=(TimeoutException,))
    def _get_tiktok_request(self, url):
        web_driver = get_web_driver()
        try:
            web_driver.get(url)

            wait = WebDriverWait(web_driver, 2)
            wait.until(lambda x: "__UNIVERSAL_DATA_FOR_REHYDRATION__" in x.page_source)
            page_content = web_driver.page_source
        finally:
            cookies = web_driver.get_cookies()
            headers = get_web_driver_headers(web_driver)
            web_driver.quit()
        return page_content, cookies, headers

    def get_video(self, url) -> VideoData:

        try:
            page_source, cookies, headers = self._get_tiktok_request(url)
        except TimeoutException:
            raise PWarning("Подозрение на \"странный\" контент. Сообщите разработчику")

        bs4 = BeautifulSoup(page_source, "html.parser")
        if any([self.AGE_RESTRICTION_MESSAGE in x.text for x in bs4.find_all("p")]):
            raise PWarning("Не могу скачать контент, так как он недоступен без аутентификации (возрастное ограничение)")

        script_data = bs4.find(id="__UNIVERSAL_DATA_FOR_REHYDRATION__")
        data = json.loads(script_data.text)
        video_detail = data['__DEFAULT_SCOPE__'].get('webapp.video-detail')
        self.raise_on_errors(video_detail)

        if video_detail:
            return self.get_video_post(video_detail, cookies, headers)
        else:
            raise PWarning("Не нашёл видео в тиктоке. Если это пост-слайдер, то я не умею их скачивать")

    def raise_on_errors(self, video_detail):
        if video_detail['statusCode'] in self.errors:
            raise PWarning(self.errors[video_detail['statusCode']])

    @staticmethod
    def get_video_post(video_detail, cookies, headers):
        video_data = video_detail['itemInfo']['itemStruct']

        cookies = {cookie['name']: cookie['value'] for cookie in cookies}

        headers["range"] = 'bytes=0-'
        headers["accept-encoding"] = 'identity;q=1, *;q=0'
        headers["referer"] = 'https://www.tiktok.com/'

        return VideoData(
            title=None,
            description=video_data.get('desc'),
            thumbnail_url=video_data['video']['originCover'],
            width=video_data['video']['width'],
            height=video_data['video']['height'],
            duration=video_data['video']['duration'],
            video_download_url=video_data['video']['playAddr'],
            extra_data={
                'cookies': cookies,
                'headers': headers,
            }
        )

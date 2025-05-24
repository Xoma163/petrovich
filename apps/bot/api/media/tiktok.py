import json

from bs4 import BeautifulSoup
from selenium.common import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from apps.bot.api.media.data import VideoData
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.proxy import get_proxies
from apps.bot.utils.utils import retry
from apps.bot.utils.web_driver import get_web_driver


class TikTok:

    @retry(times=5, exceptions=(TimeoutException,))
    def _get_tiktok_request(self, url, proxy):
        web_driver = get_web_driver(proxy=proxy)
        try:
            web_driver.get(url)

            wait = WebDriverWait(web_driver, 2)
            wait.until(lambda x: "__UNIVERSAL_DATA_FOR_REHYDRATION__" in x.page_source)
            page_content = web_driver.page_source
        finally:
            cookies = web_driver.get_cookies()
            web_driver.quit()
        return page_content, cookies

    def get_video(self, url) -> VideoData:
        proxy = get_proxies()['https'].replace('socks5h', 'socks5')

        try:
            page_source, cookies = self._get_tiktok_request(url, proxy)
        except TimeoutException:
            raise PWarning("Подозрение на \"странный\" контент. Сообщите разработчику")

        bs4 = BeautifulSoup(page_source, "html.parser")
        script_data = bs4.find(id="__UNIVERSAL_DATA_FOR_REHYDRATION__")
        data = json.loads(script_data.text)
        video_detail = data['__DEFAULT_SCOPE__'].get('webapp.video-detail')
        if video_detail:
            return self.get_video_post(video_detail, cookies)
        else:
            raise PWarning("Не нашёл видео в тиктоке. Если это пост-слайдер, то я не умею их скачивать")

    def get_video_post(self, video_detail, cookies):
        video_data = video_detail['itemInfo']['itemStruct']
        return VideoData(
            title=None,
            description=video_data.get('desc'),
            thumbnail_url=video_data['video']['originCover'],
            width=video_data['video']['width'],
            height=video_data['video']['height'],
            duration=video_data['video']['duration'],
            video_download_url=video_data['video']['playAddr'],
            extra_data={'cookies': {cookie['name']: cookie['value'] for cookie in cookies}}
        )

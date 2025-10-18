import json
import re

from bs4 import BeautifulSoup
from selenium.common import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from apps.bot.api.media.instagram import InstagramAPIData
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.decorators import retry
from apps.bot.utils.proxy import get_proxies
from apps.bot.utils.web_driver import get_web_driver


class InstagramParser:
    AGE_RESTRICTION_RE = r"You must be (\d+) years old or over to"
    INAPPROPRIATE_CONTENT = "This content may be inappropriate"

    def get_data(self, url):
        is_post = bool(re.search(r"p/([A-Za-z0-9_-]+)", url))
        is_story = bool(re.search(r"stories/.*/(\d+)", url))
        is_reel = bool(re.search(r"reels?/([A-Za-z0-9_-]+)/", url))

        if is_story:
            raise PWarning("Парсинг сторей не работает")

        proxy = get_proxies()['https'].replace('socks5h', 'socks5')

        try:
            page_source = self._get_instagram_request(url, proxy)
        except TimeoutException:
            raise PWarning(
                "Убедитесь в браузере(инкогнито), что по ссылке фото/видео и доступно к просмотру. "
                "Если это так, то сообщите разработчику"
            )
        bs4 = BeautifulSoup(page_source, "html.parser")
        spans = bs4.find_all("span")
        if any([re.search(self.AGE_RESTRICTION_RE, x.text) for x in spans]):
            raise PWarning("Не могу скачать контент, так как он недоступен без аутентификации (возрастное ограничение)")
        elif any(self.INAPPROPRIATE_CONTENT in x.text for x in spans):
            raise PWarning("Не могу скачать контент, так как он недоступен без аутентификации (неприемлимый контент)")

        try:
            all_scripts = bs4.select('script[type="application/json"][data-content-len][data-processed]')
            api_scripts = [x for x in all_scripts if 'xdt_api__v1__' in x.text]
            media = self._get_media(api_scripts)
        except Exception:
            media = self.get_media_by_parse_json(page_source)

        return self._parse_media(media)

    @retry(times=5, exceptions=(TimeoutException,))
    def _get_instagram_request(self, url, proxy):
        web_driver = get_web_driver(proxy=proxy)
        try:
            web_driver.get(url)

            # wait = WebDriverWait(web_driver, 2)
            # decline_btn = wait.until(
            #     EC.element_to_be_clickable(
            #         (By.XPATH, "//button[contains(text(), 'Decline optional cookies')]")
            #     )
            # )
            # decline_btn.click()

            wait = WebDriverWait(web_driver, 2)
            wait.until(lambda x: "xdt_api__v1__" in x.page_source)
            page_content = web_driver.page_source
        finally:
            web_driver.quit()
        return page_content

    @staticmethod
    def _get_media(api_scripts):
        for script in api_scripts:
            json_data = json.loads(script.text)
            try:
                json_data = json_data['require'][0][3][0]['__bbox']['require'][0][3][1]['__bbox']['result']['data']
                if shortcode_web_info := json_data.get('xdt_api__v1__media__shortcode__web_info'):
                    return shortcode_web_info['items'][0]
                elif clips_on_logged_out := json_data.get('xdt_api__v1__clips__clips_on_logged_out_connection_v2'):
                    return clips_on_logged_out['edges'][0]['node']['media']
            except (KeyError, IndexError):
                continue

        raise PWarning("Не могу скачать этот контент. Неизвестный тип. Сообщите разработчику")

    def get_media_by_parse_json(self, page_source):
        try:
            json_data = self.extract_json(page_source, "xdt_api__v1__media__shortcode__web_info")
            return json_data['items'][0]
        except:
            pass

        try:
            json_data = self.extract_json(page_source, 'xdt_api__v1__clips__clips_on_logged_out_connection_v2')
            return json_data['edges'][0]['node']['media']
        except:
            pass

        raise PWarning("Не могу скачать этот контент. Неизвестный тип. Сообщите разработчику")

    @staticmethod
    def _parse_media(media):
        data = InstagramAPIData()
        caption = media.get('caption')
        if caption:
            data.caption = caption.get('text', None)

        if carousel_item := media.get('carousel_media'):
            for carousel_item in carousel_item:
                if video := carousel_item.get('video_versions'):
                    data.add_video(download_url=video[0]['url'], thumbnail_url=carousel_item.get('display_uri'))
                elif image := carousel_item.get('image_versions2'):
                    data.add_image(download_url=image['candidates'][0]['url'])
        elif video := media.get('video_versions'):
            data.add_video(download_url=video[0]['url'], thumbnail_url=media.get('display_uri'))
        elif image := media.get('image_versions2'):
            data.add_image(download_url=image['candidates'][0]['url'])
        return data

    @staticmethod
    def extract_json(text, key):
        start_idx = text.find(key)
        if start_idx == -1:
            raise ValueError("Ключ не найден")
        brace_start = text.find("{", start_idx)
        if brace_start == -1:
            raise ValueError("Не найдена открывающая скобка после фразы")

        stack = 0
        for i in range(brace_start, len(text)):
            if text[i] == "{":
                stack += 1
            elif text[i] == "}":
                stack -= 1
                if stack == 0:
                    end_idx = i + 1
                    break
        else:
            raise ValueError("Баланс скобок не найден")

        json_str = text[brace_start:end_idx]
        return json.loads(json_str)

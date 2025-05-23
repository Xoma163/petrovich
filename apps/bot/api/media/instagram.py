import os
import re
from pathlib import Path

from instagrapi import Client
from instagrapi.exceptions import LoginRequired, MediaNotFound

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

    def add_video(self, download_url: str):
        item = InstagramAPIDataItem(
            content_type=InstagramAPIDataItem.CONTENT_TYPE_VIDEO,
            download_url=download_url
        )
        self.add_item(item)

    def add_image(self, download_url: str):
        item = InstagramAPIDataItem(
            content_type=InstagramAPIDataItem.CONTENT_TYPE_IMAGE,
            download_url=download_url
        )
        self.add_item(item)


class Instagram:
    LOGIN = env.str("INSTAGRAM_LOGIN")
    PASSWORD = env.str("INSTAGRAM_PASSWORD")
    TOTP_SEED = env.str("INSTAGRAM_TOTP_SEED")
    TOTP_BACKUP_CODES = env.list("INSTAGRAM_TOTP_BACKUP_CODES")

    SESSION_FILE = "secrets/instagram_session.json"

    def __init__(self):
        self.client = Client()
        self._init_client()
        self.login()

    def _init_client(self):
        instagram_app_version = "269.0.0.18.75"
        android_version = 35
        android_release = "15.0.0"
        dpi = "500dpi"
        resolution = "3088x1440"
        device_manufacturer = "samsung"
        device_name = "SM-S908E"
        device_model = "Galaxy S22 Ultra"
        cpu = "qcom"
        version_code = "314665256"

        locale = "nl_NL"
        country = "NL"
        country_code = 31

        user_agent = f"Instagram {instagram_app_version} Android ({android_version}/{android_release}; {dpi}; {resolution}; {device_manufacturer}; {device_name}; {device_model}; {cpu}; {locale}; 314665256)"
        self.client.set_user_agent(user_agent)

        device = {
            "app_version": instagram_app_version,
            "android_version": android_version,
            "android_release": android_release,
            "dpi": dpi,
            "resolution": resolution,
            "manufacturer": device_manufacturer,
            "device": device_name,
            "model": device_model,
            "cpu": cpu,
            "version_code": version_code,
        }
        self.client.set_device(device)

        self.client.set_locale(locale)
        self.client.set_country(country)
        self.client.set_country_code(country_code)

        self.client.set_proxy(get_proxies()['https'])

    def login(self):
        if os.path.exists(self.SESSION_FILE):
            self._login_with_session()
        else:
            self._login_without_session()

    def _login_with_session(self):
        self.client.load_settings(Path(self.SESSION_FILE))
        self.client.login(self.LOGIN, self.PASSWORD, verification_code=self.totp_get_code())
        print('ok login session file')

    def _login_without_session(self):
        self.client.login(self.LOGIN, self.PASSWORD, verification_code=self.totp_get_code())
        self.client.dump_settings(Path(self.SESSION_FILE))
        print('ok login without session file')

    def relogin(self):
        self.client.login(self.LOGIN, self.PASSWORD, relogin=True, verification_code=self.totp_get_code())
        self.client.dump_settings(Path(self.SESSION_FILE))
        print('ok relogin')

    def totp_enable(self):
        """
        Запускается однократно для генерации сида и бэкап ключей
        """

        seed = self.client.totp_generate_seed()
        code = self.client.totp_generate_code(seed)
        backup_codes = self.client.totp_enable(code)
        print(f"seed = {seed}")
        print(f"backup_codes = {backup_codes}")

    def totp_get_code(self):
        return self.client.totp_generate_code(self.TOTP_SEED)

    def get_data(self, instagram_link) -> InstagramAPIData:
        match = re.search(r"stories/.*/(\d+)", instagram_link)
        if match:
            media_pk = match.group(1)
        else:
            media_pk = self.client.media_pk_from_url(instagram_link)

        # Получить данные
        try:
            media_info = self.client.media_info_v1(media_pk)
        except MediaNotFound:
            raise PWarning("Медиа не найдена или закрытый аккаунт")
        except LoginRequired:
            self.relogin()
            try:
                media_info = self.client.media_info_v1(media_pk)
            except LoginRequired:
                raise PWarning("Ошибка аутентификации. Пните разраба. Не пинайте больше инсту, а то забанят акк((")

        return self._parse_response(media_info)

    @staticmethod
    def _parse_response(item) -> InstagramAPIData:
        data = InstagramAPIData()
        data.caption = item.caption_text
        product_type = item.product_type

        if product_type == 'carousel_container':
            for resource in item.resources:
                if resource.video_url:
                    data.add_video(str(resource.video_url))
                elif resource.thumbnail_url:
                    data.add_image(str(resource.thumbnail_url))
        elif product_type in ['story', 'clips', 'feed']:
            if item.video_url:
                data.add_video(str(item.video_url))
            elif item.image_versions2:
                image_url = item.image_versions2['candidates'][0]['url']
                data.add_image(str(image_url))
        else:
            raise PWarning(f"Неизвестный product_type \"{product_type}\". Сообщите разработчику")

        return data

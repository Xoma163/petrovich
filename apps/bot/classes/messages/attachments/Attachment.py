import copy
import os
from io import BytesIO
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

import requests

from apps.bot.classes.consts.Exceptions import PWarning


class Attachment:

    def __init__(self, _type):
        self.type = _type
        # Публичная ссылка для скачивания файла
        self.public_download_url = None
        # Приватная ссылка для скачивания файла
        self.private_download_url = None
        # vk/youtube links
        self.url = None
        # bytes
        self.content = None
        # len(bytes)
        self.size = None

    def set_private_download_url_tg(self, tg_bot, file_id):
        file_path = tg_bot.requests.get('getFile', params={'file_id': file_id}).json()['result']['file_path']
        self.private_download_url = f'https://{tg_bot.API_TELEGRAM_URL}/file/bot{tg_bot.token}/{file_path}'

    def prepare_obj(self, file_like_object, allowed_exts_url=None, filename=None):
        """
        Подготовка объектов(в основном картинок) для загрузки.
        То есть метод позволяет преобразовывать почти из любого формата
        """
        # url
        if isinstance(file_like_object, str) and urlparse(file_like_object).hostname:
            if allowed_exts_url:
                extension = file_like_object.split('.')[-1].lower()
                is_default_extension = extension not in allowed_exts_url
                is_vk_image = 'userapi.com' in urlparse(file_like_object).hostname
                if is_default_extension and not is_vk_image:
                    raise PWarning(f"Загрузка по URL доступна только для {' '.join(allowed_exts_url)}")
            self.public_download_url = file_like_object
        elif isinstance(file_like_object, bytes):
            if filename:
                tmp = NamedTemporaryFile()
                tmp.write(file_like_object)
                tmp.name = filename
                tmp.seek(0)
                self.content = tmp
            else:
                self.content = file_like_object
        # path
        elif isinstance(file_like_object, str) and os.path.exists(file_like_object):
            with open(file_like_object, 'rb') as file:
                file_like_object = file.read()
                self.content = file_like_object
        elif isinstance(file_like_object, BytesIO):
            file_like_object.seek(0)
            _bytes = file_like_object.read()
            if filename:
                tmp = NamedTemporaryFile()
                tmp.write(_bytes)
                tmp.name = filename
                tmp.seek(0)
                self.content = tmp
            else:
                self.content = _bytes

    def parse_response(self, attachment, allowed_exts_url=None, filename=None):
        self.prepare_obj(attachment, allowed_exts_url=allowed_exts_url, filename=filename)

    def get_download_url(self):
        return self.public_download_url if self.public_download_url else self.private_download_url

    def download_content(self) -> bytes:
        if not self.content:
            self.content = requests.get(self.get_download_url()).content
            self.size = len(self.content)
        return self.content

    def to_log(self):
        dict_self = copy.copy(self.__dict__)
        ignore_fields = ['private_download_url', 'content']
        for ignore_field in ignore_fields:
            del dict_self[ignore_field]
        return dict_self

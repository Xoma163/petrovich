import copy
import io
import os
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper  # noqa
from urllib.parse import urlparse

import requests
from PIL.Image import Image as PILImage
from django.db.models.fields.files import FieldFile

from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.proxy import get_proxies


class Attachment:
    CHUNK_SIZE = 2 ** 24  # 16mb
    ACTIVITY = None

    def __init__(self, _type, **kwargs):
        self.type: str | None = _type

        super().__init__(**kwargs)

        # Публичная ссылка для скачивания файла
        self.public_download_url: str | None = None
        # Приватная ссылка для скачивания файла
        self.private_download_url: str | None = None
        # Приватный путь для файла. Доступно только для локального сервера TgBot
        self.private_download_path: str | None = None
        self.size: int | None = 0
        # bytes
        self.content = None
        self.ext: str | None = None
        # tg
        self.file_id: str | None = None
        self.file_name: str | None = None
        self.file_name_full: str | None = None

        self.name: str | None = None

    def get_file(self, peer_id=None):
        from apps.bot.classes.bots.tg_bot import TgBot
        tg_bot = TgBot()

        size = self.get_size_mb()
        if size and size > tg_bot.MAX_ATTACHMENT_SIZE_MB:
            return

        with ChatActivity(tg_bot, self.ACTIVITY, peer_id):
            r = tg_bot.requests.get('getFile', params={'file_id': self.file_id})
            if r.status_code != 200:
                return
            file_path = r.json()['result']['file_path']
            if tg_bot.MODE == tg_bot.LOCAL_SERVER:
                self.private_download_path = file_path
            else:
                self.private_download_url = f'https://{tg_bot.requests.API_TELEGRAM_URL}/file/bot{tg_bot.token}/{file_path}'
            self.ext = file_path.rsplit('.')[-1]

    def parse(self, file_like_object, allowed_exts_url=None, filename=None, guarantee_url=False):
        """
        Подготовка объектов(в основном картинок) для загрузки.
        То есть метод позволяет преобразовывать почти из любого формата
        """
        self.name = filename
        # url
        parsed_url = None
        if isinstance(file_like_object, str):
            parsed_url = urlparse(file_like_object)
        if guarantee_url:
            self.public_download_url = file_like_object
        elif parsed_url and parsed_url.hostname:
            if allowed_exts_url:
                extension = parsed_url.path.split('.')[-1].lower()
                if extension not in allowed_exts_url:
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
        elif isinstance(file_like_object, PILImage):
            img_byte_arr = io.BytesIO()
            file_like_object.save(img_byte_arr, format="PNG")
            img_byte_arr.seek(0)
            self.content = img_byte_arr.read()
        elif isinstance(file_like_object, FieldFile):
            self.content = file_like_object.file.read()
        elif isinstance(file_like_object, _TemporaryFileWrapper):
            self.content = file_like_object.file.read()
            file_like_object.file.seek(0)
        # elif isinstance(file_like_object, types.GeneratorType):
        #     self.content = file_like_object

    def _get_download_url(self, peer_id=None):
        if self.public_download_url:
            return self.public_download_url
        if not self.private_download_url:
            self.get_file(peer_id)
        return self.private_download_url

    @staticmethod
    def _download_chunk(
            url: str,
            start: int,
            end: int,
            proxies: dict | None = None,
            headers: dict | None = None
    ) -> bytes:
        _headers = {'Range': f'bytes={start}-{end}'}
        _headers.update(headers)

        response = requests.get(url, headers=_headers, stream=True, proxies=proxies)
        return response.content

    def download_content(
            self,
            peer_id: str | int = None,
            use_proxy: bool = False,
            headers: dict | None = None,
            stream: bool = False,
            chunk_size: int | None = None
    ) -> bytes:
        if self.content:
            return self.content

        from apps.bot.utils.utils import get_default_headers
        _headers = get_default_headers()
        if headers:
            _headers.update(headers)

        download_url = self._get_download_url(peer_id)
        if self.private_download_path:
            try:
                with open(self.private_download_path, 'rb') as file:
                    self.content = file.read()
            finally:
                self.delete_download_path_file()
        else:
            proxies = get_proxies() if use_proxy else {}
            if chunk_size:
                response = requests.head(download_url, proxies=proxies)
                file_size = int(response.headers['Content-Length'])
                ranges = [(i, min(i + chunk_size - 1, file_size - 1)) for i in range(0, file_size, chunk_size)]

                with ThreadPoolExecutor() as executor:
                    chunks = executor.map(lambda r: self._download_chunk(download_url, r[0], r[1], proxies, _headers),
                                          ranges)
                self.content = b''.join(chunks)

            elif stream:
                self.content = requests.get(download_url, proxies=proxies, headers=_headers, stream=True).iter_content(
                    self.CHUNK_SIZE)
            else:
                self.content = requests.get(download_url, proxies=proxies, headers=_headers).content

        if self.name:
            tmp = NamedTemporaryFile()
            tmp.write(self.content)
            tmp.name = self.name
            tmp.seek(0)
            self.content = tmp
        return self.content

    def get_bytes_io_content(self, peer_id=None) -> BytesIO:
        return BytesIO(self.download_content(peer_id))

    def delete_download_path_file(self):
        if os.path.exists(self.private_download_path):
            os.remove(self.private_download_path)
            self.private_download_path = None

    def get_size(self) -> float | None:
        if not self.size and self.content:
            try:
                self.size = len(self.content)
            except TypeError:
                self.size = self.content.seek(0, 2)
                self.content.seek(0)
        return self.size

    def get_size_mb(self) -> float | None:
        size = self.get_size()
        if not size:
            return None
        return size / 1024 / 1024

    def to_log(self) -> dict:
        """
        Вывод в логи
        """
        dict_self = copy.copy(self.__dict__)
        ignore_fields = ["private_download_url", "content"]
        for ignore_field in ignore_fields:
            dict_self[ignore_field] = '*' * 5 if dict_self[ignore_field] else dict_self[ignore_field]
        return dict_self

    def to_api(self) -> dict:
        """
        Вывод в API
        """
        dict_self = copy.copy(self.__dict__)
        ignore_fields = ['private_download_url']
        for ignore_field in ignore_fields:
            dict_self[ignore_field] = '*' * 5 if dict_self[ignore_field] else dict_self[ignore_field]
        return dict_self

    def set_file_id(self):
        from apps.bot.classes.bots.tg_bot import TgBot
        tg_bot = TgBot()
        self.file_id = tg_bot.get_file_id(self)

    def get_file_id(self):
        if not self.file_id:
            self.set_file_id()
        return self.file_id

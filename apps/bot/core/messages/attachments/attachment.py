import base64
import copy
import os
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

import requests
from urllib3.exceptions import SSLError

from apps.bot.core.chat_action_sender import ChatActionSender
from apps.shared.decorators import retry


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
        self.content: bytes | None = None
        # filename
        self.ext: str | None = None
        self.file_name: str | None = None
        self.file_name_full: str | None = None
        # tg
        self.file_id: str | None = None

    def get_file(self, peer_id=None):
        from apps.bot.core.bot.telegram.tg_bot import TgBot
        tg_bot = TgBot()

        size = self.get_size_mb()
        if size and size > tg_bot.max_attachment_size_mb:
            return

        with ChatActionSender(tg_bot, self.ACTIVITY, peer_id):
            r = tg_bot.api_handler.get_file(self.file_id)

        if not r.get('ok'):
            return
        file_path = r['result']['file_path']
        if tg_bot.api_handler.is_local_server_mode:
            self.private_download_path = file_path
        else:
            self.private_download_url = tg_bot.api_handler.get_private_download_url(file_path)
        self._set_file_name(file_path)

    def _set_file_name(self, file_path: str):
        path = Path(file_path)
        self.file_name_full = path.name
        parts = self.file_name_full.split('.')
        if len(parts) > 2:
            self.file_name = ".".join(parts[0])
            self.ext = ".".join(parts[1:])
        else:
            self.file_name = parts[0]
            self.ext = parts[1] if len(parts) == 2 else None

    def parse(self, url=None, path=None, _bytes: bytes = None, filename=None):
        """
        Подготовка объектов(в основном картинок) для загрузки.
        То есть метод позволяет преобразовывать почти из любого формата
        """
        if not url and not path and not _bytes:
            raise ValueError("url or path or _bytes must be provided")

        if filename:
            self._set_file_name(filename)

        if url:
            self.public_download_url = url

        elif _bytes:
            if isinstance(_bytes, BytesIO):
                _bytes.seek(0)
                _bytes = _bytes.read()
            self.content = _bytes

        elif path:
            with open(path, 'rb') as file:
                file_like_object = file.read()
                self.content = file_like_object

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
            headers: dict | None = None,
            cookies: dict | None = None
    ) -> bytes:
        _headers = {'Range': f'bytes={start}-{end}'}
        _headers.update(headers)

        response = requests.get(url, headers=_headers, stream=True, cookies=cookies)
        return response.content

    @retry(3, SSLError, sleep_time=2)
    def download_content(
            self,
            peer_id: str | int = None,
            headers: dict | None = None,
            stream: bool = False,
            chunk_size: int | None = None,
            cookies: dict | None = None,
    ) -> bytes:
        if self.content:
            return self.content

        if not cookies:
            cookies = {}

        from apps.connectors.utils import get_default_headers
        _headers = get_default_headers()
        if headers is not None:
            _headers = headers

        download_url = self._get_download_url(peer_id)

        if self.private_download_path:
            try:
                with open(self.private_download_path, 'rb') as file:
                    self.content = file.read()
            finally:
                self.delete_download_path_file()
        else:
            if chunk_size:
                response = requests.head(download_url, cookies=cookies, headers=_headers)
                file_size = int(response.headers['Content-Length'])
                ranges = [(i, min(i + chunk_size - 1, file_size - 1)) for i in range(0, file_size, chunk_size)]

                with ThreadPoolExecutor() as executor:
                    chunks = executor.map(
                        lambda r: self._download_chunk(download_url, r[0], r[1], _headers, cookies),
                        ranges)
                self.content = b''.join(chunks)

            elif stream:
                chunks = []
                request = requests.get(download_url, headers=_headers, cookies=cookies, stream=True)
                for chunk in request.iter_content(self.CHUNK_SIZE):
                    chunks.append(chunk)
                self.content = b''.join(chunks)
            else:
                self.content = requests.get(download_url, headers=_headers, cookies=cookies).content

        # if self.file_name:
        #     tmp = NamedTemporaryFile()
        #     tmp.write(self.content)
        #     tmp.name = self.file_name
        #     tmp.seek(0)
        #     self.content = tmp
        return self.content

    def get_bytes_io_content(self, peer_id=None) -> BytesIO:
        _bytes = self.download_content(peer_id)
        _bytes_io = BytesIO(_bytes)
        if self.file_name_full:
            _bytes_io.name = self.file_name_full
        return _bytes_io

    def delete_download_path_file(self):
        if os.path.exists(self.private_download_path):
            os.remove(self.private_download_path)
            self.private_download_path = None

    def get_size(self) -> float | None:
        if not self.size and self.content:
            self.size = len(self.content)
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
        ignore_fields = ["private_download_url", "content", "thumbnail_bytes"]
        for ignore_field in ignore_fields:
            if ignore_field not in dict_self:
                continue
            dict_self[ignore_field] = '*' * 5 if dict_self[ignore_field] else dict_self[ignore_field]
        return dict_self

    def to_api(self) -> dict:
        """
        Вывод в API
        """
        dict_self = copy.copy(self.__dict__)
        ignore_fields = ['private_download_url', 'content']
        for ignore_field in ignore_fields:
            dict_self[ignore_field] = '*' * 5 if dict_self[ignore_field] else dict_self[ignore_field]
        return dict_self

    def set_file_id(self):
        from apps.bot.core.bot.telegram.tg_bot import TgBot
        tg_bot = TgBot()
        self.file_id = tg_bot.get_file_id(self)

    def get_file_id(self):
        if not self.file_id:
            self.set_file_id()
        return self.file_id

    def base64(self) -> str:
        self.download_content()
        return base64.b64encode(self.content).decode('utf-8')

    @staticmethod
    def decode_base64(encoded_str: str) -> bytes:
        return base64.b64decode(encoded_str)

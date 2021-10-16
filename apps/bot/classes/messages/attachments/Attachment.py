import os
from io import BytesIO
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

from apps.bot.classes.consts.Exceptions import PWarning


class Attachment:

    def __init__(self, att_type):
        self.type = att_type
        self.public_download_url = None
        self.private_download_url = None
        self.content = None
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
            self.content = _bytes

    def parse_response(self, attachment, allowed_exts=None, filename=None):
        self.prepare_obj(attachment, allowed_exts)

    def get_download_url(self):
        return self.public_download_url if self.public_download_url else self.private_download_url

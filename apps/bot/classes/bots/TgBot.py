import json
import threading
import time

import requests

from apps.bot.classes.bots.Bot import Bot as CommonBot
from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum, TG_ACTIVITIES
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.events.TgEvent import TgEvent
from apps.bot.classes.messages.ResponseMessage import ResponseMessageItem
from apps.bot.classes.messages.attachments.DocumentAttachment import DocumentAttachment
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.utils.utils import get_thumbnail_for_image, get_chunks
from petrovich.settings import env

API_TELEGRAM_URL = 'api.telegram.org'


class TgBot(CommonBot):
    API_TELEGRAM_URL = API_TELEGRAM_URL

    def __init__(self):
        CommonBot.__init__(self, Platform.TG)

        self.token = env.str("TG_TOKEN")
        self.requests = TgRequests(self.token)
        self.longpoll = MyTgBotLongPoll(self.token, self.requests)

    def listen(self):
        """
        Получение новых событий и их обработка
        """
        for raw_event in self.longpoll.listen():
            tg_event = TgEvent(raw_event, self)
            threading.Thread(target=self.handle_event, args=(tg_event,)).start()

    def _send_media_group(self, rm: ResponseMessageItem, default_params):
        media = []
        for attachment in rm.attachments:
            media.append({'type': attachment.type, 'media': attachment.public_download_url, 'caption': rm.text})
        del default_params['caption']
        default_params['media'] = json.dumps(media)
        return self.requests.get('sendMediaGroup', default_params)

    def _send_photo(self, rm: ResponseMessageItem, default_params):
        photo: PhotoAttachment = rm.attachments[0]
        if photo.public_download_url:
            default_params['photo'] = photo.public_download_url
            return self.requests.get('sendPhoto', default_params)
        else:
            return self.requests.get('sendPhoto', default_params, files={'photo': photo.content})

    def _send_document(self, rm: ResponseMessageItem, default_params):
        document: DocumentAttachment = rm.attachments[0]
        if document.public_download_url:
            default_params['document'] = document.public_download_url
            return self.requests.get('sendDocument', default_params)
        else:
            files = {'document': document.content}
            try:
                files['thumb'] = get_thumbnail_for_image(document, size=320)
            except:
                pass
            return self.requests.get('sendDocument', default_params, files=files)

    def _send_video(self, rm: ResponseMessageItem, default_params):
        video: VideoAttachment = rm.attachments[0]
        if video.public_download_url:
            default_params['video'] = video.public_download_url
            return self.requests.get('sendVideo', default_params)
        else:
            return self.requests.get('sendVideo', default_params, files={'video': video.content})

    def send_message(self, rm: ResponseMessageItem, **kwargs):
        """
        Отправка сообщения
        """
        params = {'chat_id': rm.peer_id, 'caption': rm.text, 'reply_markup': rm.keyboard}
        params.update(kwargs)
        if rm.attachments:
            if len(rm.attachments) > 1:
                return self._send_media_group(rm, params)
            elif isinstance(rm.attachments[0], PhotoAttachment):
                return self._send_photo(rm, params)
            elif isinstance(rm.attachments[0], VideoAttachment):
                return self._send_video(rm, params)
            elif isinstance(rm.attachments[0], DocumentAttachment):
                return self._send_document(rm, params)
        params['text'] = params.pop('caption')
        return self.requests.get('sendMessage', params)

    @staticmethod
    def upload_photos(images, max_count=10):
        """
        Загрузка фотографий на сервер ТГ.
        images: список изображений в любом формате (ссылки, байты, файлы)
        При невозможности загрузки одной из картинки просто пропускает её
        """
        if not isinstance(images, list):
            images = [images]
        attachments = []
        for image in images:
            try:
                pa = PhotoAttachment()
                pa.parse_response(image, ['jpg', 'jpeg', 'png'])
                attachments.append(pa)
            except Exception:
                continue
            if len(attachments) >= max_count:
                break
        return attachments

    @staticmethod
    def upload_video(video, peer_id=None, title="Видео", filename=None):
        va = VideoAttachment()
        va.parse_response(video, filename=filename)
        return va

    @staticmethod
    def upload_document(document, peer_id=None, title='Документ', filename=None):
        da = DocumentAttachment()
        da.parse_response(document, filename=filename)
        return da

    @staticmethod
    def get_inline_keyboard(buttons: list, cols=1):
        """
        Получение инлайн-клавиатуры с одной кнопкой
        В основном используется для команд, где нужно запускать много команд и лень набирать заново
        """

        def get_buttons(_buttons):
            return [{
                'text': button_item['button_text'],
                'callback_data': json.dumps({
                    'command': button_item['command'],
                    "args": button_item.get('args'),
                }, ensure_ascii=False)
            } for button_item in _buttons]

        for i, _ in enumerate(buttons):
            if 'args' not in buttons[i] or buttons[i]['args'] is None:
                buttons[i]['args'] = {}
        buttons_chunks = get_chunks(buttons, cols)
        return {
            'inline_keyboard': [get_buttons(chunk) for chunk in buttons_chunks]
        }

    def set_activity(self, peer_id, activity: ActivitiesEnum):
        """
        Метод позволяет указать пользователю, что бот набирает сообщение или записывает голосовое
        Используется при длительном выполнении команд, чтобы был фидбек пользователю, что его запрос принят
        """
        tg_activity = TG_ACTIVITIES[activity]
        self.requests.get('sendChatAction', {'chat_id': peer_id, 'action': tg_activity})


class TgRequests:
    def __init__(self, token):
        self.token = token

    def get(self, method_name, params=None, **kwargs):
        url = f'https://{API_TELEGRAM_URL}/bot{self.token}/{method_name}'
        return requests.get(url, params, **kwargs)

    def post(self, method_name, params=None, **kwargs):
        url = f'https://{API_TELEGRAM_URL}/bot{self.token}/{method_name}'
        return requests.post(url, params, **kwargs)


class MyTgBotLongPoll:
    def __init__(self, token, request=None):
        self.token = token
        if request is None:
            self.request = TgRequests(token)
        else:
            self.request = request

        self.last_update_id = 1
        self._get_last_update_id()

    def _get_last_update_id(self):
        """
        Запоминание последнего обработанного собщения
        """
        result = self.request.get('getUpdates')
        if result.status_code == 200:
            result = result.json()['result']
            if len(result) > 0:
                self.last_update_id = result[-1]['update_id'] + 1

    def check(self):
        """
        Проверка на новое сообщение
        """
        result = self.request.get('getUpdates', {'offset': self.last_update_id, 'timeout': 30}, timeout=35)
        if result.status_code != 200:
            return []
        result = result.json()['result']
        return result

    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
                    self.last_update_id = event['update_id'] + 1
                time.sleep(0.5)

            except Exception as e:
                error = {'exception': f'Longpoll Error (TG): {str(e)}'}
                print(error)

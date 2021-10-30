import json
import threading
import time

import requests

from apps.bot.classes.bots.Bot import Bot as CommonBot
from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum, TG_ACTIVITIES
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PError, PWarning
from apps.bot.classes.events.TgEvent import TgEvent
from apps.bot.classes.messages.ResponseMessage import ResponseMessageItem, ResponseMessage
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

    # MAIN ROUTING AND MESSAGING

    def listen(self):
        """
        Получение новых событий и их обработка
        """
        for raw_event in self.longpoll.listen():
            tg_event = TgEvent(raw_event, self)
            threading.Thread(target=self.handle_event, args=(tg_event,)).start()

    def _send_media_group(self, rm: ResponseMessageItem, default_params):
        """
        Отправка множества вложений. Ссылки
        """
        media = []
        for attachment in rm.attachments:
            media.append({'type': attachment.type, 'media': attachment.public_download_url, 'caption': rm.text})
        del default_params['caption']
        default_params['media'] = json.dumps(media)
        return self.requests.get('sendMediaGroup', default_params)

    def _send_photo(self, rm: ResponseMessageItem, default_params):
        """
        Отправка фото. Ссылка или файл
        """
        self.set_activity(default_params['chat_id'], ActivitiesEnum.UPLOAD_PHOTO)
        photo: PhotoAttachment = rm.attachments[0]
        if photo.public_download_url:
            default_params['photo'] = photo.public_download_url
            return self.requests.get('sendPhoto', default_params)
        else:
            return self.requests.get('sendPhoto', default_params, files={'photo': photo.content})

    def _send_document(self, rm: ResponseMessageItem, default_params):
        """
        Отправка документа. Ссылка или файл
        """
        self.set_activity(default_params['chat_id'], ActivitiesEnum.UPLOAD_DOCUMENT)
        document: DocumentAttachment = rm.attachments[0]
        if document.public_download_url:
            default_params['document'] = document.public_download_url
            return self.requests.get('sendDocument', default_params)
        else:
            files = {'document': document.content}
            try:
                files['thumb'] = get_thumbnail_for_image(document, size=320)
            except Exception:
                pass
            return self.requests.get('sendDocument', default_params, files=files)

    def _send_video(self, rm: ResponseMessageItem, default_params):
        """
        Отправка видео. Ссылка или файл
        """
        self.set_activity(default_params['chat_id'], ActivitiesEnum.UPLOAD_VIDEO)
        video: VideoAttachment = rm.attachments[0]
        if video.public_download_url:
            default_params['video'] = video.public_download_url
            return self.requests.get('sendVideo', default_params)
        else:
            if video.get_size_mb() > 40:
                rm.attachments = []
                raise PError("Нельзя загружать видео более 40 мб в телеграмм")
            return self.requests.get('sendVideo', default_params, files={'video': video.content})

    def _send_text(self, default_params):
        self.set_activity(default_params['chat_id'], ActivitiesEnum.TYPING)
        default_params['text'] = default_params.pop('caption')
        return self.requests.get('sendMessage', default_params)

    def send_response_message(self, rm: ResponseMessage):
        """
        Отправка ResponseMessage сообщения
        """
        for msg in rm.messages:
            try:
                response = self.send_message(msg)
                # Непредвиденная ошибка
                if response.status_code != 200:
                    error_msg = "Непредвиденная ошибка. Сообщите разработчику. Команда /баг"
                    error_rm = ResponseMessage(error_msg, msg.peer_id).messages[0]
                    self.logger.error({'result': error_msg, 'error': response.json()['description']})
                    self.send_message(error_rm)
            # Предвиденная ошибка
            except (PWarning, PError) as e:
                msg.text += f"\n\n{str(e)}"
                getattr(self.logger, e.level)({'result': msg})
                self.send_message(msg)

    def send_message(self, rm: ResponseMessageItem, **kwargs):
        """
        Отправка сообщения
        """
        params = {'chat_id': rm.peer_id, 'caption': rm.text, 'reply_markup': json.dumps(rm.keyboard)}
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
        return self._send_text(params)

    # END  MAIN ROUTING AND MESSAGING

    # EXTRA
    @staticmethod
    def get_inline_keyboard(buttons: list, cols=1):
        """
        param buttons: [(button_name, args), ...]
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

        # no wait for response
        try:
            self.requests.get('sendChatAction', {'chat_id': peer_id, 'action': tg_activity}, timeout=0.000001)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            pass

    @staticmethod
    def get_mention(user, name=None):
        """
        Получение меншона пользователя
        """
        if user.nickname:
            return f"@{user.nickname}"
        return str(user)

    def delete_message(self, peer_id, message_id):
        """
        Удаление одного сообщения
        """
        self.requests.get('deleteMessage', params={'chat_id': peer_id, 'message_id': message_id})

    # END EXTRA


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

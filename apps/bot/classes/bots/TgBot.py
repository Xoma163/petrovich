import json
import os
import threading
import time
import traceback
from io import BytesIO
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

import requests
from django.contrib.auth.models import Group

from apps.bot.classes.Consts import Role, Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.bots.CommonBot import CommonBot
from apps.bot.classes.common.CommonMethods import get_thumbnail_for_image
from apps.bot.classes.events.TgEvent import TgEvent
from apps.bot.models import Users, Chat, Bot
from petrovich.settings import env

API_TELEGRAM_URL = 'api.telegram.org'


class TgRequests:
    def __init__(self, token):
        self.token = token

    def get(self, method_name, params=None, **kwargs):
        url = f'https://{API_TELEGRAM_URL}/bot{self.token}/{method_name}'
        return requests.get(url, params, **kwargs)

    def post(self, method_name, params=None, **kwargs):
        url = f'https://{API_TELEGRAM_URL}/bot{self.token}/{method_name}'
        return requests.post(url, params, **kwargs)


class TgBot(CommonBot):
    def __init__(self):
        CommonBot.__init__(self, Platform.TG)

        self.token = env.str("TG_TOKEN")
        self.requests = TgRequests(self.token)
        self.longpoll = MyTgBotLongPoll(self.token, self.requests)

        self.test_chat = Chat.objects.get(pk=env.str("TG_TEST_CHAT_ID"))

    def set_activity(self, peer_id, activity='typing'):
        """
        Метод позволяет указать пользователю, что бот набирает сообщение или записывает голосовое
        Используется при длительном выполнении команд, чтобы был фидбек пользователю, что его запрос принят
        """
        if activity not in ['typing', 'audiomessage']:
            raise PWarning("Не знаю такого типа активности")
        if activity == 'audiomessage':
            activity = 'record_audio'
        self.requests.get('sendChatAction', {'chat_id': peer_id, 'action': activity})

    def register_user(self, user) -> Users:
        """
        Регистрация пользователя если его нет в БД
        Почти аналог get_user_by_id в VkBot, только у ТГ нет метода для получения данных о пользователе,
        поэтому метод немного другой
        """

        def set_fields(_user):
            _user.name = user.get('first_name', None)
            _user.surname = user.get('last_name', None)
            _user.nickname = user.get('username', None)
            _user.platform = self.platform.name
            _user.save()
            group_user = Group.objects.get(name=Role.USER.name)
            _user.groups.add(group_user)
            _user.save()

        tg_user = self.user_model.filter(user_id=user['id'])
        if len(tg_user) > 0:
            tg_user = tg_user.first()

            if tg_user.name is None:
                set_fields(tg_user)
        else:
            tg_user = Users()
            tg_user.user_id = user['id']
            set_fields(tg_user)
        return tg_user

    def get_user_by_id(self, user_id) -> Users:
        """
        Возвращает пользователя по его id
        """
        tg_user = self.user_model.filter(user_id=user_id)
        if len(tg_user) > 0:
            tg_user = tg_user.first()
        else:
            # Если пользователь из fwd
            tg_user = Users()
            tg_user.user_id = user_id
            tg_user.platform = self.platform.name

            tg_user.save()

            group_user = Group.objects.get(name=Role.USER.name)
            tg_user.groups.add(group_user)
            tg_user.save()
        return tg_user

    def get_chat_by_id(self, chat_id) -> Chat:
        """
        Возвращает чат по его id
        """
        if chat_id > 0:
            chat_id *= -1
        tg_chat = self.chat_model.filter(chat_id=chat_id)
        if len(tg_chat) > 0:
            tg_chat = tg_chat.first()
        else:
            tg_chat = Chat(chat_id=chat_id, platform=self.platform.name)
            tg_chat.save()
        return tg_chat

    def get_bot_by_id(self, bot_id) -> Bot:
        """
        Получение бота по его id
        """
        if bot_id > 0:
            bot_id = -bot_id
        bot = self.bot_model.filter(bot_id=bot_id)
        if len(bot) > 0:
            bot = bot.first()
        else:
            # Прозрачная регистрация
            bot = Bot(bot_id=bot_id, platform=self.platform.name)
            bot.save()

        return bot

    def _send_media_group(self, peer_id, msg, attachments, keyboard):
        """
        Отправка множества картинок одним сообщением
        attachments: url only
        """
        media = []
        for attachment in attachments:
            media.append({'type': attachment['type'], 'media': attachment['attachment'], 'caption': msg})
        self.requests.get('sendMediaGroup', {'chat_id': peer_id, 'media': json.dumps(media), 'reply_markup': keyboard})

    def _send_photo(self, peer_id, msg, photo, keyboard):
        """
        Отправка картинки
        photo: url или байты
        """
        if isinstance(photo, str) and urlparse(photo).hostname:
            self.requests.get('sendPhoto',
                              {'chat_id': peer_id, 'caption': msg, 'photo': photo, 'reply_markup': keyboard})
        else:
            self.requests.get('sendPhoto', {'chat_id': peer_id, 'caption': msg, 'reply_markup': keyboard},
                              files={'photo': photo})

    def _send_document(self, peer_id, msg, document, keyboard):
        """
        Отправка документа
        document: url или байты
        """
        if isinstance(document, str) and urlparse(document).hostname:
            self.requests.get('sendDocument',
                              {'chat_id': peer_id, 'caption': msg, 'document': document, 'reply_markup': keyboard})
        else:
            files = {'document': document}
            try:
                files['thumb'] = get_thumbnail_for_image(document, size=320)
            except:
                pass
            self.requests.get('sendDocument', {'chat_id': peer_id, 'caption': msg, 'reply_markup': keyboard},
                              files=files)

    def _send_video(self, peer_id, msg, video, keyboard):
        """
        Отправка видео
        video: url или байты
        """
        if isinstance(video, str) and urlparse(video).hostname:
            self.requests.get('sendVideo',
                              params={'chat_id': peer_id, 'caption': msg, 'reply_markup': keyboard, 'video': video})
        else:
            self.requests.get('sendVideo', params={'chat_id': peer_id, 'caption': msg, 'reply_markup': keyboard},
                              files={'video': video})

    def send_message(self, peer_id, msg='', attachments=None, keyboard=None, dont_parse_links=False, **kwargs):
        """
        Отправка сообщения
        peer_id: в какой чат/какому пользователю
        msg: сообщение
        attachments: список вложений
        keyboard: клавиатура
        """
        if keyboard:
            keyboard = json.dumps(keyboard)
        if attachments:
            if not isinstance(attachments, list):
                attachments = [attachments]
            # Убираем все ссылки, потому что телега в них не умеет похоже
            attachments = list(filter(lambda x: not (isinstance(x, str) and urlparse(x).hostname), attachments))
            attachments = list(filter(lambda x: x, attachments))
            if attachments:
                if len(attachments) > 1 and attachments[0]:
                    return self._send_media_group(peer_id, msg, attachments, keyboard)
                elif attachments[0]['type'] == 'video':
                    return self._send_video(peer_id, msg, attachments[0]['attachment'], keyboard)
                elif attachments[0]['type'] == 'photo':
                    return self._send_photo(peer_id, msg, attachments[0]['attachment'], keyboard)
                elif attachments[0]['type'] == 'document':
                    return self._send_document(peer_id, msg, attachments[0]['attachment'], keyboard)
        prepared_message = {'chat_id': peer_id, 'text': msg, 'parse_mode': 'HTML', 'reply_markup': keyboard}
        return self.requests.get('sendMessage', params=prepared_message)

    def _set_image_private_download_url(self, image_attachment):
        file_path = self.requests.get('getFile', params={'file_id': image_attachment['id']}).json()['result'][
            'file_path']
        image_attachment['private_download_url'] = f'https://{API_TELEGRAM_URL}/file/bot{self.token}/{file_path}'

    @staticmethod
    def _set_image_content(image_attachment):
        response = requests.get(image_attachment['private_download_url'])
        image_attachment['content'] = response.content

    def _setup_event_attachments(self, event):
        """
        Проставляет вложения для события
        """

        def _add_photo(_photo):
            _new_photo = {
                'id': _photo['file_id'],
                'tg_url': '',
                'content': '',
                'private_download_url': '',
                'download_url': None,
                'size': {},
                'type': 'photo'
            }
            if 'width' in _photo and 'height' in _photo:
                _new_photo['width'] = _photo['width']
                _new_photo['height'] = _photo['height']
            self._set_image_private_download_url(_new_photo)
            self._set_image_content(_new_photo)
            return _new_photo

        attachments = []
        if 'media_group_id' in event:
            pass
        if 'photo' in event['message']:
            # ебучая телега шлёт хуй пойми как картинки
            photo = event['message']['photo'][-1]
            new_photo = _add_photo(photo)
            attachments.append(new_photo)
        if 'voice' in event['message']:
            attachments.append(event['message']['voice'])
            attachments[-1]['type'] = 'audio_message'
            file_path = self.requests.get('getFile', params={'file_id': attachments[-1]['file_id']}).json()['result'][
                'file_path']
            attachments[-1]['private_download_url'] = f'https://{API_TELEGRAM_URL}/file/bot{self.token}/{file_path}'
        if 'document' in event['message']:
            if event['message']['document']['mime_type'] in ['image/png', 'image/jpg', 'image/jpeg']:
                photo = event['message']['document']
                new_photo = _add_photo(photo)
                attachments.append(new_photo)
        return attachments

    def _setup_event_before(self, event):
        """
        Подготовка события перед проверкой на то, нужен ли ответ
        """
        if 'callback_query' in event:
            event = event['callback_query']
            event['message']['from'] = event['from']
        tg_event = {
            'platform': self.platform,
            # ToDo key message error when message is edited
            'user_id': event['message']['from']['id'],
            'chat_id': None,
            'peer_id': event['message']['chat']['id'],
            'message': {
                'id': event['message']['message_id'],
                'text': event['message'].get('text', None) or event['message'].get('caption', None) or "",
                'attachments': [],
                'action': None,
                'payload': event.get('data', None),
                'fwd': event['message'].get('forward_from', None)
            },
            'fwd': None,
        }

        if 'new_chat_members' in event['message']:
            tg_event['message']['action'] = {
                'type': 'chat_invite_user',
                'member_ids': [],
            }
            for member in event['message']['new_chat_members']:
                if member['is_bot']:
                    tg_event['message']['action']['member_ids'].append(-member['id'])
                else:
                    tg_event['message']['action']['member_ids'].append(member['id'])
        elif 'group_chat_created' in event['message']:
            tg_event['message']['action'] = {
                'type': 'chat_invite_user',
                'member_ids': [-env.int('TG_BOT_GROUP_ID')],
            }
        elif 'left_chat_member' in event['message'] and not event['message']['left_chat_member']['is_bot']:
            tg_event['message']['action'] = {
                'type': 'chat_kick_user',
                'member_id': event['message']['left_chat_member']['id'],
            }

        if event['message']['chat']['id'] != event['message']['from']['id']:
            tg_event['chat_id'] = -event['message']['chat']['id']
            tg_event['from_user'] = False
        else:
            tg_event['from_user'] = True
        if event['message']['from']['is_bot']:
            tg_event['chat_id'] = event['message']['chat']['id']
            tg_event['from_bot'] = True

        if 'reply_to_message' in event['message']:
            tg_event['fwd'] = [{
                'id': event['message']['reply_to_message']['message_id'],
                'text': event['message']['reply_to_message'].get('text', None) or event['message'][
                    'reply_to_message'].get('caption', None),
                'attachments': [],
                'from_id': event['message']['reply_to_message']['from']['id'],
                'date': event['message']['reply_to_message']['date'],
            }]
            if 'photo' in event['message']['reply_to_message']:
                tg_event['fwd'][0]['attachments'].append(event['message']['reply_to_message']['photo'][-1])
                tg_event['fwd'][0]['attachments'][-1]['type'] = 'photo'
                tg_event['fwd'][0]['attachments'][-1]['id'] = tg_event['fwd'][0]['attachments'][-1]['file_id']
                self._set_image_private_download_url(tg_event['fwd'][0]['attachments'][-1])
                self._set_image_content(tg_event['fwd'][0]['attachments'][-1])
            if 'voice' in event['message']['reply_to_message']:
                atts = tg_event['fwd'][0]['attachments']
                atts.append(event['message']['reply_to_message']['voice'])

                atts[-1]['type'] = 'audio_message'
                file_path = self.requests.get('getFile', params={'file_id': atts[-1]['file_id']}).json()['result'][
                    'file_path']
                atts[-1]['private_download_url'] = f'https://{API_TELEGRAM_URL}/file/bot{self.token}/{file_path}'
            if event['message']['reply_to_message']['from']['is_bot']:
                tg_event['fwd'][0]['from_id'] *= -1
        tg_event['message']['attachments'] = self._setup_event_attachments(event)

        if tg_event['message']['payload']:
            tg_event['message']['text'] = ""
            tg_event['message']['attachments'] = None
        if tg_event['chat_id']:
            tg_event['chat'] = self.get_chat_by_id(int(tg_event['chat_id']))
        else:
            tg_event['chat'] = None
        return tg_event

    def need_a_response(self, tg_event):
        """
        Нужен ли ответ пользователю
        """
        if not self.need_a_response_common(tg_event):
            return False

        if not self.need_reaction_for_fwd(tg_event):
            # Игнорим forward
            if tg_event['message']['fwd']:
                return False

        # Узнаём пользователя
        if tg_event['user_id'] < 0:
            self.send_message(tg_event['peer_id'], "Боты не могут общаться с Петровичем :(")
            return False
        return True

    def _setup_event_after(self, tg_event, event):
        """
        Подготовка события после проверки на то, нужен ли ответ
        Нужно это для того, чтобы не тратить ресурсы на обработку если она не будет востребована
        """
        tg_event['sender'] = self.register_user(event.get('callback_query', event)['message']['from'])
        if tg_event['sender'] and tg_event['chat']:
            self.add_chat_to_user(tg_event['sender'], tg_event['chat'])
        else:
            tg_event['chat'] = None
        return tg_event

    def listen(self):
        """
        Получение новых событий и их обработка
        """
        for event in self.longpoll.listen():
            self.parse_event(event)

    def parse_event(self, event):
        # ToDo: check
        if 'message' not in event and 'callback_query' not in event:
            return
        try:
            tg_event = self._setup_event_before(event)
            if not self.need_a_response(tg_event):
                return
            tg_event = self._setup_event_after(tg_event, event)

            tg_event_object = TgEvent(tg_event)
            threading.Thread(target=self.menu, args=(tg_event_object,)).start()
        except Exception as e:
            print(str(e))
            tb = traceback.format_exc()
            print(tb)

    @staticmethod
    def _prepare_obj_to_upload(file_like_object, allowed_exts_url=None, filename=None):
        """
        Подготовка объектов(в основном картинок) для загрузки.
        То есть метод позволяет преобразовывать почти из любого формата в необходимый для VK
        """
        # url
        if isinstance(file_like_object, str) and urlparse(file_like_object).hostname:
            if allowed_exts_url:
                extension = file_like_object.split('.')[-1].lower()
                is_default_extension = extension not in allowed_exts_url
                is_vk_image = 'userapi.com' in urlparse(file_like_object).hostname
                if is_default_extension and not is_vk_image:
                    raise PWarning(f"Загрузка по URL доступна только для {' '.join(allowed_exts_url)}")
            return file_like_object
        if isinstance(file_like_object, bytes):
            if filename:
                tmp = NamedTemporaryFile()
                tmp.write(file_like_object)
                tmp.name = filename
                tmp.seek(0)
                return tmp
            return file_like_object
        # path
        if isinstance(file_like_object, str) and os.path.exists(file_like_object):
            with open(file_like_object, 'rb') as file:
                file_like_object = file.read()
                return file_like_object
        if isinstance(file_like_object, BytesIO):
            file_like_object.seek(0)
            _bytes = file_like_object.read()
            if filename:
                tmp = NamedTemporaryFile()
                tmp.write(_bytes)
                tmp.name = filename
                tmp.seek(0)
                return tmp
            return _bytes
        return None

    def upload_photos(self, images, max_count=10):
        """
        Загрузка фотографий на сервер ТГ.
        images: список изображений в любом формате (ссылки, байты, файлы)
        При невозможности загрузки одной из картинки просто пропускает её
        """
        if not isinstance(images, list):
            images = [images]
        images_list = []
        for image in images:
            try:
                images_list.append(
                    {'type': 'photo', 'attachment': self._prepare_obj_to_upload(image, ['jpg', 'jpeg', 'png'])})
            except Exception:
                continue
            if len(images_list) >= max_count:
                break
        return images_list

    def upload_animation(self, animation, peer_id=None, title='Документ', filename=None):
        return self.upload_video(animation, peer_id, title, filename)

    def upload_video(self, video, peer_id=None, title="Видео", filename=None):
        return {'type': 'video', 'attachment': self._prepare_obj_to_upload(video, filename=filename)}

    def upload_document(self, document, peer_id=None, title='Документ', filename=None):
        """
        Загрузка документа на сервер ТГ.
        """
        return {'type': 'document', 'attachment': self._prepare_obj_to_upload(document, filename=filename)}

    @staticmethod
    def get_inline_keyboard(command_text, button_text="Ещё", args=None):
        """
        Получение инлайн-клавиатуры с одной кнопкой
        В основном используется для команд, где нужно запускать много команд и лень набирать заново
        """
        if args is None:
            args = {}
        return {
            'inline_keyboard': [[
                {
                    'text': button_text,
                    'callback_data': json.dumps({'command': command_text, "args": args}, ensure_ascii=False)
                }
            ]]
        }

    @staticmethod
    def get_group_id(_id):
        """
        Получение group_id по короткому id
        """
        return str(_id)

    @staticmethod
    def get_mention(user, name=None):
        """
        Получение меншона пользователя
        """
        if user.nickname:
            return f"@{user.nickname}"
        return str(user)

    def upload_video_by_link(self, link, name):
        """
        Загрузка видео по ссылке со стороннего ресурса
        """
        return None

    def delete_message(self, chat_id, message_id):
        self.requests.get('deleteMessage', params={'chat_id': chat_id, 'message_id': message_id})


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

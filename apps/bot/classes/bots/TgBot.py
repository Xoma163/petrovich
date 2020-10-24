import json
import os
import threading
import time
import traceback
from io import BytesIO
from threading import Thread
from urllib.parse import urlparse

import requests
from django.contrib.auth.models import Group

from apps.bot.classes.Consts import Role
from apps.bot.classes.bots.CommonBot import CommonBot
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


class TgBot(CommonBot, Thread):
    def __init__(self):
        Thread.__init__(self)
        CommonBot.__init__(self, 'tg')

        self.token = env.str("TG_TOKEN")
        self.requests = TgRequests(self.token)
        self.longpoll = MyTgBotLongPoll(self.token, self.requests)

        # self.test_chat = Chat.objects.get(pk=env.str("TG_TEST_CHAT_ID"))

    def set_activity(self, peer_id, activity='typing'):
        if activity not in ['typing', 'audiomessage']:
            raise RuntimeWarning("Не знаю такого типа активности")
        self.requests.get('sendChatAction', {'chat_id': peer_id, 'action': activity})

    def register_user(self, user):
        def set_fields(_user):
            _user.name = user.get('first_name', None)
            _user.surname = user.get('last_name', None)
            _user.nickname = user.get('username', None)
            _user.platform = self.name
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

    def get_user_by_id(self, user_id):
        tg_user = self.user_model.filter(user_id=user_id)
        if len(tg_user) > 0:
            tg_user = tg_user.first()
        else:
            # Если пользователь из fwd
            tg_user = Users()
            tg_user.user_id = user_id
            tg_user.platform = self.name

            tg_user.save()

            group_user = Group.objects.get(name=Role.USER.name)
            tg_user.groups.add(group_user)
            tg_user.save()
        return tg_user

    def get_chat_by_id(self, chat_id):
        if chat_id > 0:
            chat_id *= -1
        tg_chat = self.chat_model.filter(chat_id=chat_id)
        if len(tg_chat) > 0:
            tg_chat = tg_chat.first()
        else:
            tg_chat = Chat(chat_id=chat_id, platform=self.name)
            tg_chat.save()
        return tg_chat

    def get_bot_by_id(self, bot_id):
        if bot_id > 0:
            bot_id = -bot_id
        bot = self.bot_model.filter(bot_id=bot_id)
        if len(bot) > 0:
            bot = bot.first()
        else:
            # Прозрачная регистрация
            bot = Bot(bot_id=bot_id, platform=self.name)
            bot.save()

        return bot

    # URL Only. Bytes not supported
    def _send_media_group(self, peer_id, msg, attachments, keyboard):
        media = []
        for attachment in attachments:
            media.append({'type': attachment['type'], 'media': attachment['attachment'], 'caption': msg})
        self.requests.get('sendMediaGroup', {'chat_id': peer_id, 'media': json.dumps(media), 'reply_markup': keyboard})

    def _send_photo(self, peer_id, msg, photo, keyboard):
        if isinstance(photo, str) and urlparse(photo).hostname:
            self.requests.get('sendPhoto',
                              {'chat_id': peer_id, 'caption': msg, 'photo': photo, 'reply_markup': keyboard})
        else:
            self.requests.get('sendPhoto', {'chat_id': peer_id, 'caption': msg, 'reply_markup': keyboard},
                              files={'photo': photo})

    def _send_video(self, peer_id, msg, video, keyboard):
        if isinstance(video, str) and urlparse(video).hostname:
            self.requests.get('sendVideo',
                              params={'chat_id': peer_id, 'caption': msg, 'reply_markup': keyboard, 'video': video})
        else:
            self.requests.get('sendVideo', params={'chat_id': peer_id, 'caption': msg, 'reply_markup': keyboard},
                              files={'video': video})

    def send_message(self, peer_id, msg='', attachments=None, keyboard=None, dont_parse_links=False, **kwargs):
        if keyboard:
            keyboard = json.dumps(keyboard)
        if attachments:
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
        prepared_message = {'chat_id': peer_id, 'text': msg, 'parse_mode': 'HTML', 'reply_markup': keyboard}
        return self.requests.get('sendMessage', params=prepared_message)

    # ToDo: в TgEvent
    def _setup_event_attachments(self, event):
        attachments = []
        if 'media_group_id' in event:
            # ToDo: для 2+ вложений, но зачем?
            pass
        if 'photo' in event['message']:
            # ToDo: ебучая телега шлёт хуй пойми как картинки
            photo = event['message']['photo'][-1]
            new_photo = {
                'id': photo['file_id'],
                'tg_url': '',
                'content': '',
                'private_download_url': '',
                'download_url': None,
                'size': {
                    'width': photo['width'],
                    'height': photo['height'],
                },
                'type': 'photo'
            }
            file_path = self.requests.get('getFile', params={'file_id': new_photo['id']}).json()['result'][
                'file_path']
            new_photo['private_download_url'] = f'https://{API_TELEGRAM_URL}/file/bot{self.token}/{file_path}'

            response = requests.get(new_photo['private_download_url'])
            new_photo['content'] = response.content
            attachments.append(new_photo)
        if 'voice' in event['message']:
            for audio_message in event['message']['voice']:
                attachments.append(audio_message)
                attachments[-1]['type'] = 'audio_message'
        return attachments

    def _setup_event(self, event):
        if 'callback_query' in event:
            event = event['callback_query']
            event['message']['from'] = event['from']
        tg_event = {
            'platform': self.name,
            'user_id': event['message']['from']['id'],
            'chat_id': None,
            'peer_id': event['message']['chat']['id'],
            'message': {
                'id': event['message']['message_id'],
                'text': event['message'].get('text', None) or event['message'].get('caption', None) or "",
                # 'payload': event.message.payload,
                'attachments': [],
                'action': None,
                'payload': event.get('data', None)
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
            if 'voice' in event['message']['reply_to_message']:
                tg_event['fwd'][0]['attachments'].append(event['message']['reply_to_message']['photo'][-1])
                tg_event['fwd'][0]['attachments'][-1]['type'] = 'audio_message'

            if event['message']['reply_to_message']['from']['is_bot']:
                tg_event['fwd'][0]['from_id'] *= -1
        tg_event['message']['attachments'] = self._setup_event_attachments(event)
        return tg_event

    def listen(self):
        for event in self.longpoll.listen():
            try:
                tg_event = self._setup_event(event)

                # Игнорим forward
                if event.get('message') and event['message'].get('forward_from'):
                    continue

                if not self.need_a_response(tg_event):
                    continue

                # Узнаём пользователя
                if tg_event['user_id'] > 0:
                    tg_event['sender'] = self.register_user(event.get('callback_query', event)['message']['from'])
                else:
                    self.send_message(tg_event['peer_id'], "Боты не могут общаться с Петровичем :(")
                    continue

                if tg_event['chat_id']:
                    tg_event['chat'] = self.get_chat_by_id(int(tg_event['chat_id']))
                    if tg_event['sender'] and tg_event['chat']:
                        self.add_chat_to_user(tg_event['sender'], tg_event['chat'])
                else:
                    tg_event['chat'] = None

                tg_event_object = TgEvent(tg_event)
                thread = threading.Thread(target=self.menu, args=(tg_event_object,))
                thread.start()
            except Exception as e:
                print(str(e))
                tb = traceback.format_exc()
                print(tb)

    @staticmethod
    def _prepare_obj_to_upload(file_like_object, allowed_exts_url=None):
        # url
        if isinstance(file_like_object, str) and urlparse(file_like_object).hostname:
            if allowed_exts_url:
                if file_like_object.split('.')[-1].lower() not in allowed_exts_url:
                    raise RuntimeWarning(f"Загрузка по URL доступна только для {' '.join(allowed_exts_url)}")
            return file_like_object
        if isinstance(file_like_object, bytes):
            return file_like_object
        # path
        if isinstance(file_like_object, str) and os.path.exists(file_like_object):
            with open(file_like_object, 'rb') as file:
                file_like_object = file.read()
                return file_like_object
        if isinstance(file_like_object, BytesIO):
            file_like_object.seek(0)
            return file_like_object.read()
        return None

    def upload_photos(self, images, max_count=10):
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

    def upload_document(self, document, peer_id=None, title='Документ'):
        return {'type': 'video', 'attachment': self._prepare_obj_to_upload(document)}

    @staticmethod
    def get_inline_keyboard(command_text, button_text="Ещё", args=None):
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
        return _id

    @staticmethod
    def get_mention(user, name=None):
        if user.nickname:
            return f"@{user.nickname}"
        elif user.name:
            return user.name

    def upload_video_by_link(self, link, name):
        return None


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
        result = self.request.get('getUpdates')
        if result.status_code == 200:
            result = result.json()['result']
            if len(result) > 0:
                self.last_update_id = result[-1]['update_id'] + 1

    def check(self):
        result = self.request.get('getUpdates', {'offset': self.last_update_id, 'timeout': 30})
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

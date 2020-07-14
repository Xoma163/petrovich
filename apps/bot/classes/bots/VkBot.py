import io
import json
import logging
import os
import threading
from threading import Thread
from urllib.parse import urlparse

import requests
import urllib3
import vk_api
from django.contrib.auth.models import Group
from requests.exceptions import ReadTimeout, ConnectTimeout, SSLError
from vk_api import VkUpload, VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

from apps.bot.classes.Consts import Role
from apps.bot.classes.bots.CommonBot import CommonBot
from apps.bot.classes.bots.VkUser import VkUser
from apps.bot.classes.events.VkEvent import VkEvent
from apps.bot.commands.City import add_city_to_db
from apps.bot.models import Users, Chat
from petrovich.settings import env


class VkBot(CommonBot, Thread):
    def __init__(self):
        Thread.__init__(self)
        CommonBot.__init__(self, 'vk')

        self.token = env.str('VK_BOT_TOKEN')
        self.group_id = env.str('VK_BOT_GROUP_ID')
        vk_session = VkApi(token=self.token, api_version="5.107", config_filename="secrets/vk_bot_config.json")
        self.longpoll = MyVkBotLongPoll(vk_session, group_id=self.group_id)
        self.upload = VkUpload(vk_session)
        self.vk = vk_session.get_api()

        self.vk_user = VkUser()

        self.logger = logging.getLogger('vk_bot')

    def set_activity(self, peer_id, activity='typing'):
        if activity not in ['typing', 'audiomessage']:
            raise RuntimeWarning("Не знаю такого типа активности")
        self.vk.messages.setActivity(type=activity, peer_id=peer_id, group_id=self.group_id)

    def get_user_by_id(self, user_id):
        vk_user = self.user_model.filter(user_id=user_id)
        if len(vk_user) > 0:
            vk_user = vk_user.first()
        else:
            # Прозрачная регистрация
            user = self.vk.users.get(user_id=user_id, lang='ru', fields='sex, bdate, city, screen_name')[0]
            vk_user = Users()
            vk_user.user_id = user_id
            vk_user.name = user['first_name']
            vk_user.surname = user['last_name']
            vk_user.platform = self.name

            if 'sex' in user:
                vk_user.gender = user['sex']
            if 'bdate' in user:
                vk_user.birthday = self.parse_date(user['bdate'])
            if 'city' in user:
                from apps.service.models import City
                city_name = user['city']['title']
                city = City.objects.filter(name=city_name)
                if len(city) > 0:
                    city = city.first()
                else:
                    try:
                        city = add_city_to_db(city_name)
                    except Exception:
                        city = None
                vk_user.city = city
            else:
                vk_user.city = None
            if 'screen_name' in user:
                vk_user.nickname = user['screen_name']
            vk_user.save()
            group_user = Group.objects.get(name=Role.USER.name)
            vk_user.groups.add(group_user)
            vk_user.save()
        return vk_user
        pass

    def get_chat_by_id(self, chat_id):
        vk_chat = self.chat_model.objects.filter(chat_id=chat_id)
        if len(vk_chat) > 0:
            vk_chat = vk_chat.first()
        else:
            vk_chat = Chat(chat_id=chat_id, platform=self.name)
            vk_chat.save()
        return vk_chat

    def get_bot_by_id(self, bot_id):
        if bot_id > 0:
            bot_id = -bot_id
        bot = self.bot_model.objects.filter(bot_id=bot_id)
        if len(bot) > 0:
            bot = bot.first()
        else:
            # Прозрачная регистрация
            vk_bot = self.vk.groups.getById(group_id=bot_id)[0]

            bot = self.bot_model()
            bot.bot_id = bot_id
            bot.name = vk_bot['name']
            bot.platform = self.name
            bot.save()

        return bot

    def send_message(self, peer_id, msg="ᅠ", attachments=None, keyboard=None, dont_parse_links=False, **kwargs):
        if attachments is None:
            attachments = []
        if isinstance(attachments, str):
            attachments = [attachments]
        if attachments and msg == "ᅠ":
            msg = ""
        if keyboard:
            keyboard = json.dumps(keyboard)
        msg = str(msg)
        if len(msg) > 4096:
            msg = msg[:4092]
            msg += "\n..."
        try:
            self.vk.messages.send(peer_id=peer_id,
                                  message=msg,
                                  access_token=self.token,
                                  random_id=get_random_id(),
                                  attachment=','.join(attachments),
                                  keyboard=keyboard,
                                  dont_parse_links=dont_parse_links
                                  )
        except vk_api.exceptions.ApiError as e:
            if e.code == 901:
                pass
            else:
                print("Ошибка отправки сообщения\n"
                      f"{e}")

    def _setup_event(self, event):
        vk_event = {
            'platform': self.name,
            'from_user': event.from_user,
            'chat_id': event.chat_id,
            'user_id': event.message.from_id,
            'peer_id': event.message.peer_id,
            'message': {
                # 'id': event.message.id,
                'text': event.message.text,
                'payload': event.message.payload,
                'attachments': event.message.attachments,
                'action': event.message.action
            },
            'fwd': None
        }
        # ToDo: VK. Проверить при добавлении пользователя/бота в конфу - что будет.
        if vk_event['message'].get('action', None) and vk_event['message']['action']['type'] in [
            'chat_invite_user', 'chat_invite_user_by_link']:
            vk_event['message']['action']['members_id'] = [vk_event['message']['action'].pop('member_id')]
        return vk_event

    def listen(self):
        for event in self.longpoll.listen():
            try:
                # Если пришло новое сообщение
                if event.type == VkBotEventType.MESSAGE_NEW:
                    vk_event = self._setup_event(event)

                    # Сообщение либо мне в лс, либо упоминание меня, либо есть аудиосообщение, либо есть экшн
                    if not self.need_a_response(vk_event):
                        continue

                    # Обработка вложенных сообщений в event['fwd']. reply и fwd для вк это разные вещи.
                    if event.message.reply_message:
                        vk_event['fwd'] = [event.message.reply_message]
                    elif len(event.message.fwd_messages) != 0:
                        vk_event['fwd'] = event.message.fwd_messages

                    # Узнаём пользователя
                    if vk_event['user_id'] > 0:
                        vk_event['sender'] = self.get_user_by_id(vk_event['user_id'])
                    else:
                        self.send_message(vk_event['peer_id'], "Боты не могут общаться с Петровичем :(")
                        continue

                    # Узнаём конфу
                    if vk_event['chat_id']:
                        vk_event['chat'] = self.get_chat_by_id(int(vk_event['peer_id']))
                        if vk_event['sender'] and vk_event['chat']:
                            self.add_group_to_user(vk_event['sender'], vk_event['chat'])
                    else:
                        vk_event['chat'] = None

                    vk_event_object = VkEvent(vk_event)
                    thread = threading.Thread(target=self.menu, args=(vk_event_object,))
                    thread.start()

                    print('message')
            except:
                pass

    @staticmethod
    def _prepare_obj_to_upload(file_like_object, allowed_exts_url=None):
        # bytes array
        if isinstance(file_like_object, bytes):
            obj = io.BytesIO(file_like_object)
            obj.seek(0)
        # bytesIO
        elif isinstance(file_like_object, io.BytesIO):
            obj = file_like_object
            obj.seek(0)
        # url
        elif urlparse(file_like_object).hostname:
            if allowed_exts_url:
                if file_like_object.split('.')[-1].lower() not in allowed_exts_url:
                    raise RuntimeWarning(f"Загрузка по URL доступна только для {' '.join(allowed_exts_url)}")
            try:
                response = requests.get(file_like_object, stream=True, timeout=3)
            except SSLError:
                raise RuntimeWarning(f"SSLError")
            except requests.exceptions.ConnectionError:
                raise RuntimeWarning(f"ConnectionError")
            obj = response.raw
        # path
        else:
            obj = file_like_object
        return obj

    def _get_attachment_by_id(self, _type, group_id, _id):
        if group_id is None:
            group_id = f'-{self.group_id}'
        return f"{_type}{group_id}_{_id}"

    def upload_photos(self, images, max_count=10):
        if not isinstance(images, list):
            images = [images]

        attachments = []
        images_to_load = []
        for image in images:
            try:
                image = self._prepare_obj_to_upload(image, ['jpg', 'jpeg', 'png'])
            except RuntimeWarning:
                continue
            except ReadTimeout:
                continue
            except ConnectTimeout:
                continue
            # Если Content-Length > 50mb
            bytes_count = None
            if isinstance(image, io.BytesIO):
                bytes_count = image.getbuffer().nbytes
            elif isinstance(image, urllib3.response.HTTPResponse) or isinstance(image,
                                                                                requests.packages.urllib3.response.HTTPResponse):
                bytes_count = image.headers.get('Content-Length')
            elif os.path.exists(image):
                bytes_count = os.path.getsize(image)
            else:
                print("ШТО ТЫ ТАКОЕ", type(image))
            if not bytes_count:
                continue
            if int(bytes_count) / 1024 / 1024 > 50:
                continue
            images_to_load.append(image)

            if len(images_to_load) >= max_count:
                break
        try:
            vk_photos = self.upload.photo_messages(images_to_load)
            for vk_photo in vk_photos:
                attachments.append(self._get_attachment_by_id('photo', vk_photo['owner_id'], vk_photo['id']))
        except vk_api.exceptions.ApiError as e:
            print(e)
        return attachments

    def upload_document(self, document, peer_id=None, title='Документ'):
        document = self._prepare_obj_to_upload(document)
        vk_document = self.upload.document_message(document, title=title, peer_id=peer_id)['doc']
        return self._get_attachment_by_id('doc', vk_document['owner_id'], vk_document['id'])

    @staticmethod
    def get_inline_keyboard(command_text, button_text="Ещё", args=None):
        if args is None:
            args = {}
        return {
            'inline': True,
            'buttons': [[
                {
                    'action': {
                        'type': 'text',
                        'label': button_text,
                        "payload": json.dumps({"command": command_text, "args": args}, ensure_ascii=False)
                    },
                    'color': 'primary',
                }
            ]]}

    @staticmethod
    def get_group_id(_id):
        return 2000000000 + int(_id)

    @staticmethod
    def get_mention(user, name=None):
        name = name or str(user)
        return f"[id{user.user_id}|{name}]"

    def upload_video_by_link(self, link, name):
        values = {
            'name': name,
            'is_private': True,
            'link': link,
        }

        response = self.vk_user.vk.video.save(**values)
        response2 = requests.post(response['upload_url']).json()
        print(response2)

        return f"video{response['owner_id']}_{response['video_id']}"


class MyVkBotLongPoll(VkBotLongPoll):

    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as e:
                error = {'exception': f'Longpoll Error (VK): {str(e)}'}
                # logger.error(error)

import logging
import threading
import time
from threading import Thread

import requests
from django.contrib.auth.models import Group

from apps.bot.classes.Consts import Role
from apps.bot.classes.bots.CommonBot import CommonBot
from apps.bot.classes.events.TgEvent import TgEvent
from apps.bot.models import TgUser as TgUserModel, TgChat as TgChatModel, TgBot as TgBotModel
from petrovich.settings import env


class TgRequests:
    def __init__(self, token):
        self.token = token

    def get(self, url, params=None, **kwargs):
        url = f'https://api.telegram.org/bot{self.token}/{url}'
        return requests.get(url, params, **kwargs)


class TgBot(CommonBot, Thread):
    def __init__(self):
        CommonBot.__init__(self)
        Thread.__init__(self)

        self.token = env.str("TG_TOKEN")
        self.requests = TgRequests(self.token)
        self.longpoll = MyTgBotLongPoll(self.token, self.requests)

        self.user_model = TgUserModel
        self.chat_model = TgChatModel
        self.bot_model = TgBotModel

        # self.tg_user = TgUser()

        self.logger = logging.getLogger('tg_bot')

    def register_user(self, user):
        def set_fields(_user):
            _user.name = user.get('first_name', None)
            _user.surname = user.get('last_name', None)
            _user.nickname = user.get('username', None)
            tg_user.save()
            group_user = Group.objects.get(name=Role.USER.name)
            tg_user.groups.add(group_user)
            tg_user.save()

        tg_user = self.user_model.objects.filter(user_id=user['id'])
        if len(tg_user) > 0:
            tg_user = tg_user.first()

            if tg_user.name == "Незарегистрированный":
                set_fields(tg_user)
        else:
            tg_user = self.user_model()
            tg_user.user_id = user['id']
            set_fields(tg_user)
        return tg_user

    def get_user_by_id(self, user_id):
        tg_user = self.user_model.objects.filter(user_id=user_id)
        if len(tg_user) > 0:
            tg_user = tg_user.first()
        else:
            # Если пользователь из fwd
            tg_user = self.user_model()
            tg_user.user_id = user_id
            tg_user.name = "Незарегистрированный"
            tg_user.surname = "Пользователь"
            tg_user.save()

            group_user = Group.objects.get(name=Role.USER.name)
            tg_user.groups.add(group_user)
            tg_user.save()
        return tg_user

    def get_chat_by_id(self, chat_id):
        tg_chat = self.chat_model.objects.filter(chat_id=chat_id)
        if len(tg_chat) > 0:
            tg_chat = tg_chat.first()
        else:
            tg_chat = self.chat_model(chat_id=chat_id)
            tg_chat.save()
        return tg_chat

    def send_message(self, peer_id, msg="ᅠ", attachments=None, keyboard=None, dont_parse_links=False, **kwargs):
        prepared_message = {'chat_id': peer_id, 'text': msg}
        self.requests.get('sendMessage', params=prepared_message)

    # @bot.message_handler()
    def listen(self):
        for event in self.longpoll.listen():
            try:
                tg_event = {
                    'from_user': not event['message']['from']['is_bot'],
                    'user_id': event['message']['from']['id'],
                    'chat_id': None,
                    'peer_id': event['message']['chat']['id'],
                    'message': {
                        'id': event['message']['message_id'],
                        'text': event['message']['text'],
                        # 'payload': event.message.payload,
                        'attachments': [],
                        'action': None
                    },
                    'fwd': None
                }
                if not tg_event['from_user']:
                    tg_event['chat_id'] = event['message']['chat']['id']
                if 'reply_to_message' in event['message']:
                    tg_event['fwd'] = {
                        'id': event['message']['reply_to_message']['message_id'],
                        'text': event['message']['reply_to_message']['text'],
                    }
                # Игнорим forward
                if 'forward_from' in event['message']:
                    continue

                if not self.need_a_response(tg_event):
                    continue

                # Узнаём пользователя
                # ToDo: проверить что вернёт бот если сообщение отправит чат-бот
                if tg_event['user_id'] > 0:
                    tg_event['sender'] = self.register_user(event['message']['from'])
                else:
                    self.send_message(tg_event['peer_id'], "Боты не могут общаться с Петровичем :(")
                    continue

                # ToDo: not tested
                # Узнаём конфу
                if tg_event['chat_id']:
                    tg_event['chat'] = self.get_chat_by_id(int(tg_event['peer_id']))
                    if tg_event['sender'] and tg_event['chat']:
                        self.add_group_to_user(tg_event['sender'], tg_event['chat'])
                else:
                    tg_event['chat'] = None

                tg_event_object = TgEvent(tg_event)
                thread = threading.Thread(target=self.menu, args=(tg_event_object,))
                thread.start()
            except Exception as e:
                print(e)
                pass


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
        result = self.request.get('getUpdates', {'offset': self.last_update_id})
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
                # logger.error(error)

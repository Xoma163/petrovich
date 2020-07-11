import logging
import threading
import time
import traceback
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

            if tg_user.name is None:
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

    def get_bot_by_id(self, bot_id):
        if bot_id > 0:
            bot_id = -bot_id
        bot = self.bot_model.objects.filter(bot_id=bot_id)
        if len(bot) > 0:
            bot = bot.first()
        else:
            # Прозрачная регистрация
            bot = self.bot_model()
            bot.bot_id = bot_id
            bot.save()

        return bot

    def send_photo(self, peer_id, msg, attachments):
        prepared_photo = {'chat_id': peer_id, 'caption': msg, 'photo': attachments}
        self.requests.get('sendPhoto', params=prepared_photo)

    def send_message(self, peer_id, msg="ᅠ", attachments=None, keyboard=None, dont_parse_links=False, **kwargs):
        if attachments:
            self.send_photo(peer_id, msg, attachments)
            return
        prepared_message = {'chat_id': peer_id, 'text': msg}
        self.requests.get('sendMessage', params=prepared_message)

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
                        'text': event['message'].get('text', None) or event['message'].get('caption', None) or "",
                        # 'payload': event.message.payload,
                        'attachments': [],
                        'action': None
                    },
                    'fwd': None,
                }
                # actions
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
                if not tg_event['from_user']:
                    tg_event['chat_id'] = event['message']['chat']['id']
                if 'reply_to_message' in event['message']:
                    tg_event['fwd'] = [{
                        'id': event['message']['reply_to_message']['message_id'],
                        'text': event['message']['reply_to_message']['text'],
                        'attachments': event['message'].get('photo', None) or event['message'].get('voice', None)
                    }]
                # Игнорим forward
                if 'forward_from' in event['message']:
                    continue

                if not self.need_a_response(tg_event):
                    continue

                # Узнаём пользователя
                if tg_event['from_user']:
                    tg_event['sender'] = self.register_user(event['message']['from'])
                else:
                    self.send_message(tg_event['peer_id'], "Боты не могут общаться с Петровичем :(")
                    continue

                if tg_event['chat_id']:
                    tg_event['chat'] = self.get_chat_by_id(int(tg_event['chat_id']))
                    if tg_event['sender'] and tg_event['chat']:
                        self.add_group_to_user(tg_event['sender'], tg_event['chat'])
                else:
                    tg_event['chat'] = None

                tg_event_object = TgEvent(tg_event)
                thread = threading.Thread(target=self.menu, args=(tg_event_object,))
                thread.start()
            except Exception as e:
                print(str(e))
                tb = traceback.format_exc()
                print(tb)


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
                # logger.error(error)

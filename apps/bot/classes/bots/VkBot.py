import json
import logging
import threading
from threading import Thread

import vk_api
from django.contrib.auth.models import Group
from vk_api import VkUpload, VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

from apps.bot.classes.Consts import Role
from apps.bot.classes.bots.CommonBot import CommonBot
from apps.bot.classes.bots.VkUser import VkUser
from apps.bot.classes.events.VkEvent import VkEvent
from apps.bot.commands.City import add_city_to_db
from apps.bot.models import VkUser as VkUserModel, VkChat as VkChatModel, VkBot as VkBotModel
from petrovich.settings import env


class VkBot(CommonBot, Thread):
    def __init__(self):
        CommonBot.__init__(self)
        Thread.__init__(self)

        self._TOKEN = env.str('VK_BOT_TOKEN')
        self.group_id = env.str('VK_BOT_GROUP_ID')
        vk_session = VkApi(token=self._TOKEN, api_version="5.107", config_filename="secrets/vk_bot_config.json")
        self.longpoll = MyVkBotLongPoll(vk_session, group_id=self.group_id)
        self.upload = VkUpload(vk_session)
        self.vk = vk_session.get_api()
        self.mentions = env.list('VK_BOT_MENTIONS')

        self.vk_user = VkUser()

        self.BOT_CAN_WORK = True
        self.DEBUG = False
        self.DEVELOP_DEBUG = False

        self.user_model = VkUserModel
        self.chat_model = VkChatModel
        self.bot_model = VkBotModel

        self.logger = logging.getLogger('vk_bot')

    def get_user_by_id(self, user_id):
        vk_user = self.user_model.objects.filter(user_id=user_id)
        if len(vk_user) > 0:
            vk_user = vk_user.first()
        else:
            # Прозрачная регистрация
            user = self.vk.users.get(user_id=user_id, lang='ru', fields='sex, bdate, city, screen_name')[0]
            vk_user = self.user_model()
            vk_user.user_id = user_id
            vk_user.name = user['first_name']
            vk_user.surname = user['last_name']
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
            vk_chat = self.chat_model(chat_id=chat_id)
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
                                  access_token=self._TOKEN,
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

    def listen(self):
        for event in self.longpoll.listen():
            try:
                # Если пришло новое сообщение
                if event.type == VkBotEventType.MESSAGE_NEW:
                    vk_event = {
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


class MyVkBotLongPoll(VkBotLongPoll):

    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as e:
                error = {'exception': f'Longpoll Error (VK): {str(e)}'}
                # logger.error(error)

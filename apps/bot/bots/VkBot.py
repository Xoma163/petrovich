import json
import logging
import threading
import traceback
from threading import Thread

import vk_api
from django.contrib.auth.models import Group
from vk_api import VkUpload, VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

from apps.bot.bots.CommonBot import CommonBot
from apps.bot.bots.VkUser import VkUser
from apps.bot.classes.CommonMethods import check_user_group, get_user_groups, tanimoto
from apps.bot.classes.Consts import Role
from apps.bot.classes.VkEvent import VkEvent
from apps.bot.commands.City import add_city_to_db
from apps.bot.models import VkUser as VkUserModel, VkChat
from apps.service.views import append_command_to_statistics
from petrovich.settings import env

logger = logging.getLogger('bot')


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

    def get_user_by_id(self, user_id):
        vk_user = VkUserModel.objects.filter(user_id=user_id)
        if len(vk_user) > 0:
            vk_user = vk_user.first()
        else:
            # Прозрачная регистрация
            user = self.vk.users.get(user_id=user_id, lang='ru', fields='sex, bdate, city, screen_name')[0]
            vk_user = VkUserModel()
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

    @staticmethod
    def get_chat_by_id(chat_id):
        vk_chat = VkChat.objects.filter(chat_id=chat_id)
        if len(vk_chat) > 0:
            vk_chat = vk_chat.first()
        else:
            vk_chat = VkChat(chat_id=chat_id)
            vk_chat.save()
        return vk_chat

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

    def menu(self, vk_event, send=True):

        # Проверяем не остановлен ли бот, если так, то проверяем вводимая команда = старт?
        if not self.can_bot_working():
            if not check_user_group(vk_event.sender, Role.ADMIN):
                return

            if vk_event.command in ['старт']:
                self.BOT_CAN_WORK = True
                # cameraHandler.resume()
                msg = "Стартуем!"
                self.send_message(vk_event.peer_id, msg)
                log_result = {'result': msg}
                logger.debug(log_result)
                return msg
            return

        group = vk_event.sender.groups.filter(name=Role.BANNED.name)
        if len(group) > 0:
            return

        if self.DEBUG and send:
            if hasattr(vk_event, 'payload') and vk_event.payload:
                debug_message = \
                    f"msg = {vk_event.msg}\n" \
                    f"command = {vk_event.command}\n" \
                    f"args = {vk_event.args}\n" \
                    f"payload = {vk_event.payload}\n"
            else:
                debug_message = \
                    f"msg = {vk_event.msg}\n" \
                    f"command = {vk_event.command}\n" \
                    f"args = {vk_event.args}\n" \
                    f"original_args = {vk_event.original_args}\n"
            self.send_message(vk_event.peer_id, debug_message)

        log_vk_event = {'vk_event': vk_event}
        logger.debug(log_vk_event)

        from apps.bot.initial import get_commands
        commands = get_commands()
        for command in commands:
            try:
                if command.accept(vk_event):
                    result = command.__class__().check_and_start(self, vk_event)
                    if send:
                        self.parse_and_send_msgs(vk_event.peer_id, result)
                    append_command_to_statistics(vk_event.command)
                    log_result = {'result': result}
                    logger.debug(log_result)
                    return result
            except RuntimeWarning as e:
                msg = str(e)
                log_runtime_warning = {'result': msg}
                logger.warning(log_runtime_warning)

                if send:
                    self.parse_and_send_msgs(vk_event.peer_id, msg)
                return msg
            except RuntimeError as e:
                exception = str(e)
                log_runtime_error = {'exception': exception, 'result': exception}
                logger.error(log_runtime_error)
                if send:
                    self.parse_and_send_msgs(vk_event.peer_id, exception)
                return exception
            except Exception as e:
                msg = "Непредвиденная ошибка. Сообщите разработчику в группе или команда /баг"
                tb = traceback.format_exc()
                log_exception = {
                    'exception': str(e),
                    'result': msg
                }
                logger.error(log_exception, exc_info=tb)
                if send:
                    self.parse_and_send_msgs(vk_event.peer_id, msg)
                return msg

        if vk_event.chat and not vk_event.chat.need_reaction:
            return None
        similar_command = commands[0].names[0]
        tanimoto_max = 0
        user_groups = get_user_groups(vk_event.sender)
        for command in commands:
            # Выдача пользователю только тех команд, которые ему доступны
            command_access = command.access
            if isinstance(command_access, str):
                command_access = [command_access]
            if command_access.name not in user_groups:
                continue

            for name in command.names:
                if name:
                    tanimoto_current = tanimoto(vk_event.command, name)
                    if tanimoto_current > tanimoto_max:
                        tanimoto_max = tanimoto_current
                        similar_command = name

        msg = f"Я не понял команды \"{vk_event.command}\"\n"
        if tanimoto_max != 0:
            msg += f"Возможно вы имели в виду команду \"{similar_command}\""
        logger_result = {'result': msg}
        logger.debug(logger_result)
        if send:
            self.send_message(vk_event.peer_id, msg)
        return msg

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
                    # Сообщение либо мне в лс, либо упоминание меня, либо есть аудиосообщение, либо есть экшн
                    if not self.need_a_response(vk_event):
                        continue

                    # Обработка вложенных сообщений в vk_event['fwd']. reply и fwd для вк это разные вещи.
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

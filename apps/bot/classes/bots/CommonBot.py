import logging
import threading
import traceback

from apps.bot.classes.Consts import Role, Platform
from apps.bot.classes.common.CommonMethods import tanimoto
from apps.bot.classes.events.Event import Event
from apps.bot.models import Users, Chat, Bot
from apps.service.views import append_command_to_statistics


class CommonBot:
    def __init__(self, platform):
        self.platform = platform
        self.mentions = []
        self.BOT_CAN_WORK = True
        self.DEBUG = False
        self.DEVELOP_DEBUG = False
        self.user_model = Users.objects.filter(platform=self.platform.name)
        self.chat_model = Chat.objects.filter(platform=self.platform.name)
        self.bot_model = Bot.objects.filter(platform=self.platform.name)

        self.logger = logging.getLogger(platform.value)

    def get_user_by_id(self, user_id):
        raise NotImplementedError

    def get_chat_by_id(self, chat_id):
        raise NotImplementedError

    def get_bot_by_id(self, bot_id):
        raise NotImplementedError

    def run(self):
        self.listen()

    def listen(self):
        raise NotImplementedError

    def menu(self, event, send=True):

        # Проверяем не остановлен ли бот, если так, то проверяем вводимая команда = старт?
        if not self.can_bot_working():
            if not event.sender.check_role(Role.ADMIN):
                return

            if event.command in ['старт']:
                self.BOT_CAN_WORK = True
                # cameraHandler.resume()
                msg = "Стартуем!"
                self.send_message(event.peer_id, msg)
                log_result = {'result': msg}
                self.logger.debug(log_result)
                return msg
            return

        group = event.sender.groups.filter(name=Role.BANNED.name)
        if len(group) > 0:
            return

        if self.DEBUG and send:
            if hasattr(event, 'payload') and event.payload:
                debug_message = \
                    f"msg = {event.msg}\n" \
                    f"command = {event.command}\n" \
                    f"args = {event.args}\n" \
                    f"payload = {event.payload}\n"
            else:
                debug_message = \
                    f"msg = {event.msg}\n" \
                    f"command = {event.command}\n" \
                    f"args = {event.args}\n" \
                    f"original_args = {event.original_args}\n"
            self.send_message(event.peer_id, debug_message)

        log_event = event
        self.logger.debug(log_event)

        from apps.bot.initial import COMMANDS

        for command in COMMANDS:
            try:
                if command.accept(event):
                    result = command.__class__().check_and_start(self, event)
                    if send:
                        self.parse_and_send_msgs(event.peer_id, result)
                    append_command_to_statistics(event.command)
                    log_result = {'result': result}
                    self.logger.debug(log_result)
                    return result
            except RuntimeWarning as e:
                msg = str(e)
                log_runtime_warning = {'result': msg}
                self.logger.warning(log_runtime_warning)
                if send:
                    self.parse_and_send_msgs(event.peer_id, msg)
                return msg
            except RuntimeError as e:
                msg = str(e)
                log_runtime_error = {'exception': msg, 'result': msg}
                self.logger.error(log_runtime_error)
                if send:
                    self.parse_and_send_msgs(event.peer_id, msg)
                return msg
            except Exception as e:
                msg = "Непредвиденная ошибка. Сообщите разработчику в группе или команда /баг"
                tb = traceback.format_exc()
                log_exception = {
                    'exception': str(e),
                    'result': msg
                }
                self.logger.error(log_exception, exc_info=tb)
                if send:
                    self.parse_and_send_msgs(event.peer_id, msg)
                return msg

        if event.chat and not event.chat.need_reaction:
            return None
        similar_command = COMMANDS[0].names[0]
        tanimoto_max = 0
        user_groups = event.sender.get_list_of_role_names()
        for command in COMMANDS:
            # Выдача пользователю только тех команд, которые ему доступны
            command_access = command.access
            if isinstance(command_access, str):
                command_access = [command_access]
            if command_access.name not in user_groups:
                continue

            # Выдача только тех команд, у которых стоит флаг выдачи
            if not command.suggest_for_similar:
                continue

            for name in command.names:
                if name:
                    tanimoto_current = tanimoto(event.command, name)
                    if tanimoto_current > tanimoto_max:
                        tanimoto_max = tanimoto_current
                        similar_command = name

        msg = f"Я не понял команды \"{event.command}\"\n"
        if tanimoto_max != 0:
            msg += f"Возможно вы имели в виду команду \"{similar_command}\""
        self.logger_result = {'result': msg}
        self.logger.debug(self.logger_result)
        if send:
            self.send_message(event.peer_id, msg)
        return msg

    def send_message(self, peer_id, msg="ᅠ", attachments=None, keyboard=None, dont_parse_links=False, **kwargs):
        raise NotImplementedError

    def parse_and_send_msgs(self, peer_id, result):
        if isinstance(result, str) or isinstance(result, int) or isinstance(result, float):
            result = {'msg': result}
        if isinstance(result, dict):
            result = [result]
        if isinstance(result, list):
            for msg in result:
                if isinstance(msg, str):
                    msg = {'msg': msg}
                if isinstance(msg, dict):
                    self.send_message(peer_id, **msg)

    # Отправляет сообщения юзерам в разных потоках
    def parse_and_send_msgs_thread(self, chat_ids, message):
        if not isinstance(chat_ids, list):
            chat_ids = [chat_ids]
        for chat_id in chat_ids:
            thread = threading.Thread(target=self.parse_and_send_msgs, args=(chat_id, message,))
            thread.start()

    def need_a_response(self, event):
        message = event['message']['text']

        have_payload = 'message' in event and 'payload' in event['message'] and event['message']['payload']
        if have_payload:
            return True
        have_audio_message = self.have_audio_message(event)
        if have_audio_message:
            return True
        have_action = event['message']['action'] is not None
        if have_action:
            return True
        empty_message = len(message) == 0
        if empty_message:
            return False
        from_user = event['from_user']
        if from_user:
            return True
        message_is_command = message[0] == '/'
        if message_is_command:
            return True
        for mention in self.mentions:
            if message.find(mention) != -1:
                return True
        return False

    @staticmethod
    def have_audio_message(event):
        if isinstance(event, Event):
            all_attachments = event.attachments or []
            if event.fwd:
                all_attachments += event.fwd[0]['attachments']
            if all_attachments:
                for attachment in all_attachments:
                    if attachment['type'] == 'audio_message':
                        return True
        else:
            all_attachments = event['message']['attachments'].copy()
            if event['fwd'] and 'attachments' in event['fwd'][0]:
                all_attachments += event['fwd'][0]['attachments']
            if all_attachments:
                for attachment in all_attachments:
                    if attachment['type'] == 'audio_message':
                        # Костыль, чтобы при пересланном сообщении он не выполнял никакие другие команды
                        # event['message']['text'] = ''
                        return True
        return False

    @staticmethod
    def parse_date(date):
        date_arr = date.split('.')
        if len(date_arr) == 2:
            return f"1970-{date_arr[1]}-{date_arr[0]}"
        else:
            return f"{date_arr[2]}-{date_arr[1]}-{date_arr[0]}"

    @staticmethod
    def add_chat_to_user(user, chat):
        chats = user.chats
        if chat not in chats.all():
            chats.add(chat)

    @staticmethod
    def remove_group_from_user(user, chat):
        chats = user.chats
        if chat in chats.all():
            chats.remove(chat)

    def can_bot_working(self):
        return self.BOT_CAN_WORK

    def get_user_by_name(self, args, filter_chat=None):
        if not args:
            raise RuntimeWarning("Отсутствуют аргументы")
        if isinstance(args, str):
            args = [args]
        users = self.user_model
        if filter_chat:
            users = users.filter(chats=filter_chat)
        if len(args) >= 2:
            user = users.filter(name=args[0].capitalize(), surname=args[1].capitalize())
        else:
            user = users.filter(nickname_real=args[0].capitalize())
            if len(user) == 0:
                user = users.filter(name=args[0].capitalize())
                if len(user) == 0:
                    user = users.filter(surname=args[0].capitalize())
                    if len(user) == 0:
                        user = users.filter(nickname=args[0])
                        if len(user) == 0:
                            user = users.filter(user_id=args[0])

        if len(user) > 1:
            raise RuntimeWarning("2 и более пользователей подходит под поиск")

        if len(user) == 0:
            raise RuntimeWarning("Пользователь не найден. Возможно опечатка или он мне ещё ни разу не писал")

        return user.first()

    def get_chat_by_name(self, args, filter_platform=True):
        if not args:
            raise RuntimeWarning("Отсутствуют аргументы")
        if isinstance(args, str):
            args = [args]

        if filter_platform:
            chats = self.chat_model
        else:
            chats = Chat.objects.all()

        for arg in args:
            chats = chats.filter(name__icontains=arg)

        if len(chats) > 1:
            raise RuntimeWarning("2 и более чатов подходит под поиск")

        if len(chats) == 0:
            raise RuntimeWarning("Чат не найден")
        return chats.first()

    def upload_document(self, document, peer_id=None, title='Документ'):
        raise NotImplementedError

    def upload_photos(self, images, max_count=10):
        raise NotImplementedError

    def get_one_chat_with_user(self, chat_name, user_id):
        chats = self.chat_model.filter(name__icontains=chat_name)
        if len(chats) == 0:
            raise RuntimeWarning("Не нашёл такого чата")

        chats_with_user = []
        for chat in chats:
            user_contains = chat.users_set.filter(user_id=user_id)
            if user_contains:
                chats_with_user.append(chat)

        if len(chats_with_user) == 0:
            raise RuntimeWarning("Не нашёл доступного чата с пользователем в этом чате")
        elif len(chats_with_user) > 1:
            chats_str = '\n'.join(chats_with_user)
            raise RuntimeWarning("Нашёл несколько чатов. Уточните какой:\n"
                                 f"{chats_str}")

        elif len(chats_with_user) == 1:
            return chats_with_user[0]

    @staticmethod
    def get_gamer_by_user(user):
        from apps.games.models import Gamer

        gamers = Gamer.objects.filter(user=user)
        if len(gamers) == 0:
            gamer = Gamer(user=user)
            gamer.save()
            return gamer
        elif len(gamers) > 1:
            raise RuntimeWarning("Два и более игрока подходит под поиск")
        else:
            return gamers.first()


def get_bot_by_platform(platform: Platform):
    from apps.bot.classes.bots.VkBot import VkBot
    from apps.bot.classes.bots.TgBot import TgBot

    platforms = {
        Platform.VK: VkBot,
        Platform.TG: TgBot
    }
    return platforms[platform]

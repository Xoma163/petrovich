import logging
import traceback
from threading import Thread

from apps.bot.classes.Consts import Role, Platform
from apps.bot.classes.Exceptions import PSkip, PWarning, PError
from apps.bot.classes.common.CommonMethods import tanimoto
from apps.bot.classes.events.Event import Event
from apps.bot.models import Users, Chat, Bot
from apps.games.models import Gamer
from apps.service.models import Meme
from apps.service.views import append_command_to_statistics


class CommonBot(Thread):
    def __init__(self, platform):
        Thread.__init__(self)

        self.platform = platform
        self.mentions = []
        self.BOT_CAN_WORK = True
        self.DEBUG = False
        self.DEVELOP_DEBUG = False
        self.user_model = Users.objects.filter(platform=self.platform.name)
        self.chat_model = Chat.objects.filter(platform=self.platform.name)
        self.bot_model = Bot.objects.filter(platform=self.platform.name)

        self.logger = logging.getLogger(platform.value)

    def get_user_by_id(self, user_id) -> Users:
        """
        Возвращает пользователя по его id
        """
        raise NotImplementedError

    def get_chat_by_id(self, chat_id) -> Chat:
        """
        Возвращает чат по его id
        """
        raise NotImplementedError

    def get_bot_by_id(self, bot_id) -> Bot:
        """
        Получение бота по его id
        """
        raise NotImplementedError

    def run(self):
        """
        Thread запуск основного тела команды
        """
        self.listen()

    def listen(self):
        """
        Получение новых событий и их обработка
        """
        pass
        # raise NotImplementedError

    @staticmethod
    def _get_similar_command(event, commands):
        """
        Получение похожей команды по неправильно введённой
        """
        similar_command = None
        tanimoto_max = 0
        user_groups = event.sender.get_list_of_role_names()
        for command in commands:
            if not command.full_names:
                continue

            # Выдача пользователю только тех команд, которые ему доступны
            command_access = command.access
            if isinstance(command_access, str):
                command_access = [command_access]
            if command_access.name not in user_groups:
                continue

            # Выдача только тех команд, у которых стоит флаг выдачи
            if not command.suggest_for_similar:
                continue

            for name in command.full_names:
                if name:
                    tanimoto_current = tanimoto(event.command, name)
                    if tanimoto_current > tanimoto_max:
                        tanimoto_max = tanimoto_current
                        similar_command = name

        msg = f"Я не понял команды \"{event.command}\"\n"
        if similar_command and tanimoto_max != 0:
            msg += f"Возможно вы имели в виду команду \"{similar_command}\""
        return msg

    def menu(self, event, send=True):
        """
        Выбор команды и отправка данных о сообщении ей
        Проверки на запущенность бота, забаненных юзеров
        """
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
            except PSkip:
                return
            except PWarning as e:
                msg = str(e)
                log_runtime_warning = {'result': msg}
                self.logger.warning(log_runtime_warning)
                if send:
                    self.parse_and_send_msgs(event.peer_id, msg)
                return msg
            except PError as e:
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
        if event.chat and event.chat.mentioning:
            return None
        similar_command = self._get_similar_command(event, COMMANDS)
        self.logger.debug({'result': similar_command})
        if send:
            self.send_message(event.peer_id, similar_command)
        return similar_command

    def send_message(self, peer_id, msg="ᅠ", attachments=None, keyboard=None, dont_parse_links=False, **kwargs):
        """
        Отправка сообщения
        peer_id: в какой чат/какому пользователю
        msg: сообщение
        attachments: список вложений
        keyboard: клавиатура
        dont_parse_links: не преобразовывать ссылки
        """
        raise NotImplementedError

    @staticmethod
    def parse_command_result(result):
        """
        Преобразование 1 из 4х типов сообщения в единый стандарт
        [{...},{...}]
        """
        msgs = []
        if isinstance(result, str) or isinstance(result, int) or isinstance(result, float):
            result = {'msg': str(result)}
        if isinstance(result, dict):
            result = [result]
        if isinstance(result, list):
            for msg in result:
                if isinstance(msg, str):
                    msg = {'msg': msg}
                if isinstance(msg, dict):
                    msgs.append(msg)
        return msgs

    def parse_and_send_msgs(self, peer_id, result):
        """
        Отправка сообщения от команды. Принимает любой формат
        """
        msgs = self.parse_command_result(result)
        for msg in msgs:
            self.send_message(peer_id, **msg)

    # Отправляет сообщения юзерам в разных потоках
    def parse_and_send_msgs_thread(self, chat_ids, message):
        """
        Преобразование сообщения и отправка в отдельном потоке для каждого чата
        """
        if not isinstance(chat_ids, list):
            chat_ids = [chat_ids]
        for chat_id in chat_ids:
            thread = Thread(target=self.parse_and_send_msgs, args=(chat_id, message,))
            thread.start()

    def need_a_response_common(self, event) -> bool:
        """
        Нужен ли ответ пользователю
        Правила ответа
        """
        message = event['message']['text']

        if event['chat'] and event['chat'].is_banned:
            return False

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
        message_is_exact_meme_name = Meme.objects.filter(name__unaccent=message.lower()).exists()
        if message_is_exact_meme_name:
            return True
        for mention in self.mentions:
            if message.find(mention) != -1:
                return True
        if event['chat'] and event['chat'].mentioning:
            return True
        return False

    @staticmethod
    def have_audio_message(event) -> bool:
        """
        Есть ли аудиосообщение в сообщении
        """
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
    def parse_date(date) -> str:
        """
        Парсинг даты
        """
        date_arr = date.split('.')
        if len(date_arr) == 2:
            return f"1970-{date_arr[1]}-{date_arr[0]}"
        else:
            return f"{date_arr[2]}-{date_arr[1]}-{date_arr[0]}"

    @staticmethod
    def add_chat_to_user(user, chat):
        """
        Добавление чата пользователю
        """
        chats = user.chats
        if chat not in chats.all():
            chats.add(chat)

    @staticmethod
    def remove_chat_from_user(user, chat):
        """
        Удаление чата пользователю
        """
        chats = user.chats
        if chat in chats.all():
            chats.remove(chat)

    def can_bot_working(self) -> bool:
        """
        Запущен ли бот
        """
        return self.BOT_CAN_WORK

    # ToDo: очень говнокод
    def get_user_by_name(self, args, filter_chat=None) -> Users:
        """
        Получение пользователя по имени/фамилии/имени и фамилии/никнейма/ид
        """
        if not args:
            raise PWarning("Отсутствуют аргументы")
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
            raise PWarning("2 и более пользователей подходит под поиск")

        if len(user) == 0:
            raise PWarning("Пользователь не найден. Возможно опечатка или он мне ещё ни разу не писал")

        return user.first()

    def get_chat_by_name(self, args, filter_platform=True) -> Chat:
        """
        Получение чата по названию
        """
        if not args:
            raise PWarning("Отсутствуют аргументы")
        if isinstance(args, str):
            args = [args]

        if filter_platform:
            chats = self.chat_model
        else:
            chats = Chat.objects.all()

        for arg in args:
            chats = chats.filter(name__icontains=arg)

        if len(chats) > 1:
            raise PWarning("2 и более чатов подходит под поиск")

        if len(chats) == 0:
            raise PWarning("Чат не найден")
        return chats.first()

    def upload_photos(self, images, max_count=10):
        """
        Загрузка фотографий
        """
        raise NotImplementedError

    def upload_animation(self, animation, peer_id=None, title='Документ'):
        """
        Загрузка анимации (GIF)
        """
        raise NotImplementedError

    def upload_document(self, document, peer_id=None, title='Документ'):
        """
        Загрузка документа
        """
        raise NotImplementedError

    def get_one_chat_with_user(self, chat_name, user_id):
        """
        Получение чата по названию, в котором есть пользователь
        """
        chats = self.chat_model.filter(name__icontains=chat_name)
        if len(chats) == 0:
            raise PWarning("Не нашёл такого чата")

        chats_with_user = []
        for chat in chats:
            user_contains = chat.users.filter(user_id=user_id)
            if user_contains:
                chats_with_user.append(chat)

        if len(chats_with_user) == 0:
            raise PWarning("Не нашёл доступного чата с пользователем в этом чате")
        elif len(chats_with_user) > 1:
            chats_str = '\n'.join(chats_with_user)
            raise PWarning("Нашёл несколько чатов. Уточните какой:\n"
                           f"{chats_str}")

        elif len(chats_with_user) == 1:
            return chats_with_user[0]

    @staticmethod
    def get_gamer_by_user(user) -> Gamer:
        """
        Получение игрока по модели пользователя
        """

        gamers = Gamer.objects.filter(user=user)
        if len(gamers) == 0:
            gamer = Gamer(user=user)
            gamer.save()
            return gamer
        elif len(gamers) > 1:
            raise PWarning("Два и более игрока подходит под поиск")
        else:
            return gamers.first()


def get_bot_by_platform(platform: Platform):
    """
    Получение бота по платформе
    """
    from apps.bot.classes.bots.VkBot import VkBot
    from apps.bot.classes.bots.TgBot import TgBot
    from apps.bot.classes.bots.YandexBot import YandexBot

    platforms = {
        Platform.VK: VkBot,
        Platform.TG: TgBot,
        Platform.YANDEX: YandexBot
    }
    return platforms[platform]


def get_moderator_bot_class():
    from apps.bot.classes.bots.TgBot import TgBot
    return TgBot()

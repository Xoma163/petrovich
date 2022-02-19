import logging
import traceback
from threading import Lock
from threading import Thread
from typing import List

from django.contrib.auth.models import Group

from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.consts.Consts import Platform, Role
from apps.bot.classes.consts.Exceptions import PWarning, PError, PSkip
from apps.bot.classes.events.Event import Event
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem
from apps.bot.classes.messages.attachments.DocumentAttachment import DocumentAttachment
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.models import Profile, Chat, Bot as BotModel, User
from apps.bot.utils.utils import tanimoto, get_chunks
from apps.games.models import Gamer
from petrovich.settings import env


class Bot(Thread):
    def __init__(self, platform):
        Thread.__init__(self)

        self.platform = platform
        self.user_model = User.objects.filter(platform=self.platform.name)
        self.chat_model = Chat.objects.filter(platform=self.platform.name)
        self.bot_model = BotModel.objects.filter(platform=self.platform.name)

        self.logger = logging.getLogger(platform.name)
        self.lock = Lock()

    # MAIN ROUTING AND MESSAGING

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

    def handle_event(self, event: Event, send=True) -> ResponseMessage:
        """
        Обработка входящего ивента
        """
        try:
            event.setup_event()
            if not event.need_a_response():
                return
            message = self.route(event)
            if send:
                self.send_response_message(message)
            return message
        except PSkip:
            pass
        except Exception as e:
            print(str(e))
            tb = traceback.format_exc()
            print(tb)

    def parse_and_send_msgs(self, msgs, peer_id):
        """
        Отправка сообщений. Принимает любой формат
        """
        rm = msgs if isinstance(msgs, ResponseMessage) else ResponseMessage(msgs, peer_id)
        return self.send_response_message(rm)

    def parse_and_send_msgs_thread(self, msgs, peer_id: int):
        """
        Парсинг сырых сообщений и отправка их в отдельном потоке
        """
        Thread(target=self.parse_and_send_msgs, args=(msgs, peer_id)).start()

    def send_response_message(self, rm: ResponseMessage) -> List[dict]:
        """
        Отправка ResponseMessage сообщения
        Вовзращает список результатов отправки в формате
        [{success:bool, response:Response, response_message_item:ResponseMessageItem}]
        """
        pass
        # raise NotImplementedError

    def send_response_message_item(self, rm: ResponseMessageItem):
        """
        Отправка ResponseMessageItem сообщения
        Возвращает Response платформы
        """
        pass

    def route(self, event: Event) -> ResponseMessage:
        """
        Выбор команды
        Если в Event есть команда, поиск не требуется
        """
        # self.set_activity(event.peer_id, ActivitiesEnum.TYPING)
        from apps.bot.initial import COMMANDS

        if event.command:
            commands = [event.command()]
        else:
            commands = COMMANDS

        for command in commands:
            try:
                if command.accept(event):
                    result = command.__class__().check_and_start(self, event)
                    rm = ResponseMessage(result, event.peer_id)
                    self.logger.debug({"message": rm.to_log(), "event": event.to_log()})
                    return rm
            except (PWarning, PError) as e:
                msg = str(e)
                rm = ResponseMessage(msg, event.peer_id)
                getattr(self.logger, e.level)({"message": rm.to_log(), "event": event.to_log()})
                return rm
            except PSkip as e:
                raise e
            except Exception as e:
                msg = "Непредвиденная ошибка. Сообщите разработчику. Команда /баг"
                rm = ResponseMessage(msg, event.peer_id)
                self.logger.error({"exception": str(e), "message": rm.to_log(), "event": event.to_log()},
                                  exc_info=traceback.format_exc())
                return rm

        # Если указана настройка не реагировать на неверные команды, то скипаем
        if event.chat and not event.chat.need_reaction:
            raise PSkip()

        # Если указана настройка реагировать на команды без слеша, но команду мы не нашли, то скипаем
        # Но только в случае если нет явного упоминания нас, тогда точно даём ответ
        if event.chat and event.chat.mentioning and event.message and not event.message.mentioned:
            raise PSkip()

        similar_command = self.get_similar_command(event, COMMANDS)
        rm = ResponseMessage(similar_command, event.peer_id)
        self.logger.debug({"message": rm.to_log(), "event": event.to_log()})
        return rm

    @staticmethod
    def get_similar_command(event: Event, commands):
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
            if command_access.name not in user_groups:
                continue

            # Выдача только тех команд, у которых стоит флаг выдачи
            if not command.suggest_for_similar:
                continue

            for name in command.full_names:
                if name:
                    tanimoto_current = tanimoto(event.message.command, name)
                    if tanimoto_current > tanimoto_max:
                        tanimoto_max = tanimoto_current
                        similar_command = name

        msg = f"Я не понял команды \"{event.message.command}\"\n"
        if similar_command and tanimoto_max != 0:
            msg += f"Возможно вы имели в виду команду \"{similar_command}\""
        return msg

    # END MAIN ROUTING AND MESSAGING

    # USERS GROUPS BOTS

    def get_user_by_id(self, user_id, _defaults: dict = None) -> User:
        """
        Получение пользователя по его id
        """
        if not _defaults:
            _defaults = {}
        defaults = {}
        defaults.update(_defaults)

        with self.lock:
            user, _ = self.user_model.get_or_create(
                user_id=user_id,
                platform=self.platform.name,
                defaults=defaults
            )
        return user

    def get_profile_by_user_id(self, user_id):
        user = self.get_user_by_id(user_id)
        profile = self.get_profile_by_user(user)
        return profile

    def get_profile_by_user(self, user: User, is_new=False, _defaults: dict = None) -> Profile:
        """
        Возвращает профиль по пользователю
        """
        if not _defaults:
            _defaults = {}
        defaults = {}
        defaults.update(_defaults)

        if not user.profile:
            with self.lock:
                profile = Profile(**defaults)
                profile.save()
                user.profile = profile
                user.save()
                is_new = True

        if is_new:
            with self.lock:
                user.profile.default_platform = self.platform
                user.profile.save()

                group_user = Group.objects.get(name=Role.USER.name)
                user.profile.groups.add(group_user)
        return user.profile

    def update_profile_avatar(self, profile: Profile, user_id):
        """
        Обновление аватарки пользователя
        """
        pass

    # ToDo: очень говнокод
    @staticmethod
    def get_profile_by_name(args, filter_chat=None) -> Profile:
        """
        Получение пользователя по имени/фамилии/имени и фамилии/никнейма/ид
        """
        if not args:
            raise PWarning("Отсутствуют аргументы")
        if isinstance(args, str):
            args = [args]
        users = Profile.objects
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

        if len(user) > 1:
            raise PWarning("2 и более пользователей подходит под поиск")

        if len(user) == 0:
            raise PWarning("Пользователь не найден. Возможно опечатка или он мне ещё ни разу не писал")

        return user.first()

    def get_chat_by_id(self, chat_id: int) -> Chat:
        """
        Возвращает чат по его id
        """
        with self.lock:
            chat, _ = self.chat_model.get_or_create(
                chat_id=chat_id, platform=self.platform.name
            )
        return chat

    def get_bot_by_id(self, bot_id: int) -> BotModel:
        """
        Возвращает бота по его id
        """
        if bot_id > 0:
            bot_id = -bot_id
        with self.lock:
            bot, _ = self.bot_model.get_or_create(
                bot_id=bot_id, platform=self.platform.name
            )
        return bot

    def get_gamer_by_profile(self, profile: Profile) -> Gamer:
        """
        Получение игрока по модели пользователя
        """
        with self.lock:
            gamer, _ = Gamer.objects.get_or_create(profile=profile)
        return gamer

    def add_chat_to_profile(self, profile: Profile, chat: Chat):
        """
        Добавление чата пользователю
        """
        with self.lock:
            chats = profile.chats
            if chat not in chats.all():
                chats.add(chat)

    def remove_chat_from_profile(self, profile: Profile, chat: Chat):
        """
        Удаление чата пользователю
        """
        with self.lock:
            chats = profile.chats
            if chat in chats.all():
                chats.remove(chat)

    # END USERS GROUPS BOTS

    # ATTACHMENTS
    def upload_photos(self, images, max_count=10, peer_id=None):
        """
        Загрузка фотографий на сервер ТГ.
        images: список изображений в любом формате (ссылки, байты, файлы)
        При невозможности загрузки одной из картинки просто пропускает её
        """
        if not isinstance(images, list):
            images = [images]
        attachments = []
        for image in images:
            try:
                if peer_id:
                    self.set_activity(peer_id, ActivitiesEnum.UPLOAD_PHOTO)
                pa = PhotoAttachment()
                pa.parse_response(image, ['jpg', 'jpeg', 'png'])
                attachments.append(pa)
            except Exception:
                continue
            if len(attachments) >= max_count:
                break
        return attachments

    def upload_document(self, document, peer_id=None, title='Документ', filename=None):
        """
        Загрузка документа
        """
        if peer_id:
            self.set_activity(peer_id, ActivitiesEnum.UPLOAD_DOCUMENT)
        da = DocumentAttachment()
        da.parse_response(document, filename=filename)
        return da

    def upload_video(self, document, peer_id=None, title='Документ', filename=None):
        """
        Загрузка гифки
        """
        if peer_id:
            self.set_activity(peer_id, ActivitiesEnum.UPLOAD_VIDEO)
        va = VideoAttachment()
        va.parse_response(document, filename=filename)
        return va

    # END ATTACHMENTS

    # EXTRA
    def set_activity(self, peer_id, activity: ActivitiesEnum):
        pass

    @staticmethod
    def _get_keyboard_buttons(buttons):
        """
        Определение структуры кнопок. Переопределяется в каждом боте
        """
        pass

    def get_inline_keyboard(self, buttons: list, cols=1):
        """
        param buttons: ToDo:
        Получение инлайн-клавиатуры с кнопками
        В основном используется для команд, где нужно запускать много команд и лень набирать заново
        """
        for i, _ in enumerate(buttons):
            if 'args' not in buttons[i] or buttons[i]['args'] is None:
                buttons[i]['args'] = {}
        buttons_chunks = get_chunks(buttons, cols)
        keyboard = [self._get_keyboard_buttons(chunk) for chunk in buttons_chunks]
        return keyboard

    def get_mention(self, profile: Profile, name=None):
        pass

    def delete_message(self, peer_id, message_id):
        pass

    # END EXTRA


def get_bot_by_platform(platform: Platform):
    """
    Получение бота по платформе
    """
    from apps.bot.classes.bots.vk.VkBot import VkBot
    from apps.bot.classes.bots.tg.TgBot import TgBot
    from apps.bot.classes.bots.yandex.YandexBot import YandexBot

    platforms = {
        Platform.VK: VkBot,
        Platform.TG: TgBot,
        Platform.YANDEX: YandexBot
    }
    return platforms[platform]()


def send_message_to_moderator_chat(msgs):
    def get_moderator_chat_peer_id():
        test_chat_id = env.str("TG_MODERATOR_CHAT_PK")
        return Chat.objects.get(pk=test_chat_id).chat_id

    def get_moderator_bot_class():
        from apps.bot.classes.bots.tg.TgBot import TgBot
        return TgBot

    bot = get_moderator_bot_class()()
    peer_id = get_moderator_chat_peer_id()
    return bot.parse_and_send_msgs(msgs, peer_id)


def upload_image_to_vk_server(image):
    vk_bot = get_bot_by_platform(Platform.VK)
    photos = vk_bot.upload_photos(image, 1)
    return photos[0].public_download_url

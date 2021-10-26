import logging
import traceback
from threading import Thread

from django.contrib.auth.models import Group

from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.consts.Consts import Platform, Role
from apps.bot.classes.consts.Exceptions import PWarning, PError, PSkip
from apps.bot.classes.events.Event import Event
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem
from apps.bot.classes.messages.attachments.DocumentAttachment import DocumentAttachment
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.models import Users, Chat, Bot as BotModel
from apps.bot.utils.utils import tanimoto
from apps.games.models import Gamer
from petrovich.settings import env


class Bot(Thread):
    def __init__(self, platform):
        Thread.__init__(self)

        self.platform = platform
        self.mentions = []
        self.user_model = Users.objects.filter(platform=self.platform.name)
        self.chat_model = Chat.objects.filter(platform=self.platform.name)
        self.bot_model = BotModel.objects.filter(platform=self.platform.name)

        self.logger = logging.getLogger(platform.value)

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

    def handle_event(self, event: Event, send=True):
        """
        Обработка входящего ивента
        """
        try:
            event.setup_event()
            if not event.need_a_response():
                return
            message = self.route(event)
            if message:
                self.parse_and_send_msgs(event.peer_id, message, send)
        except Exception as e:
            print(str(e))
            tb = traceback.format_exc()
            print(tb)

    def parse_and_send_msgs(self, peer_id, msgs, send=True) -> ResponseMessage:
        """
        Отправка сообщений. Принимает любой формат
        """
        rm = ResponseMessage(msgs, peer_id)
        if send:
            self.send_response_message(rm)
        return rm

    def parse_and_send_msgs_thread(self, peer_id: int, msgs: list):
        """
        Парсинг сырых сообщений и отправка их в отдельном потоке
        """
        Thread(target=self.parse_and_send_msgs, args=(peer_id, msgs)).start()

    def send_response_message(self, rm: ResponseMessage):
        """
        Отправка ResponseMessage сообщения
        """
        raise NotImplementedError

    def send_message(self, rm: ResponseMessageItem):
        """
        Отправка сообщения
        """
        raise NotImplementedError

    def route(self, event: Event):
        """
        Выбор команды
        Если в Event есть команда, поиск не требуется
        """
        self.logger.debug(event.to_log())
        from apps.bot.initial import COMMANDS

        if event.command:
            commands = [event.command()]
        else:
            commands = COMMANDS

        for command in commands:
            try:
                if command.accept(event):
                    result = command.__class__().check_and_start(self, event)
                    self.logger.debug({'result': result})
                    return result
            except (PWarning, PError) as e:
                msg = str(e)
                getattr(self.logger, e.level)({'result': msg})
                return msg
            except PSkip:
                return
            except Exception as e:
                msg = "Непредвиденная ошибка. Сообщите разработчику. Команда /баг"
                log_exception = {
                    'exception': str(e),
                    'result': msg
                }
                self.logger.error(log_exception, exc_info=traceback.format_exc())
                return msg

        # Если указана настройка не реагировать на неверные команды, то скипаем
        if event.chat and not event.chat.need_reaction:
            return

        # Если указана настройка реагировать на команды без слеша, но команду мы не нашли, то скипаем
        if event.chat and event.chat.mentioning:
            return

        similar_command = self.get_similar_command(event, COMMANDS)
        self.logger.debug({'result': similar_command})
        return similar_command

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

    def get_user_by_id(self, user_id: int, _defaults: dict = None) -> Users:
        """
        Возвращает пользователя по его id
        """
        if not _defaults:
            _defaults = {}
        defaults = {'platform': self.platform.name}
        defaults.update(_defaults)

        user, created = self.user_model.get_or_create(
            user_id=user_id,
            platform=self.platform.name,
            defaults=defaults
        )
        if created or user.name is None:
            group_user = Group.objects.get(name=Role.USER.name)
            user.groups.add(group_user)
            user.save()
        return user

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

    def get_chat_by_id(self, chat_id: int) -> Chat:
        """
        Возвращает чат по его id
        """
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
        bot, _ = self.bot_model.get_or_create(
            bot_id=bot_id, platform=self.platform.name
        )
        return bot

    @staticmethod
    def get_gamer_by_user(user: Users) -> Gamer:
        """
        Получение игрока по модели пользователя
        """
        gamer, _ = Gamer.objects.get_or_create(user=user)
        return gamer

    @staticmethod
    def add_chat_to_user(user: Users, chat: Chat):
        """
        Добавление чата пользователю
        """
        chats = user.chats
        if chat not in chats.all():
            chats.add(chat)

    @staticmethod
    def remove_chat_from_user(user: Users, chat: Chat):
        """
        Удаление чата пользователю
        """
        chats = user.chats
        if chat in chats.all():
            chats.remove(chat)

    # END USERS GROUPS BOTS

    # ATTACHMENTS
    def upload_photos(self, images, max_count=10):
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
                pa = PhotoAttachment()
                pa.parse_response(image, ['jpg', 'jpeg', 'png'])
                attachments.append(pa)
            except Exception:
                continue
            if len(attachments) >= max_count:
                break
        return attachments

    @staticmethod
    def upload_document(document, peer_id=None, title='Документ', filename=None):
        """
        Загрузка документа
        """
        da = DocumentAttachment()
        da.parse_response(document, filename=filename)
        return da

    @staticmethod
    def upload_video(document, peer_id=None, title='Документ', filename=None):
        """
        Загрузка гифки
        """
        va = VideoAttachment()
        va.parse_response(document, filename=filename)
        return va

    # END ATTACHMENTS

    def set_activity(self, peer_id, activity: ActivitiesEnum):
        pass

    @staticmethod
    def get_inline_keyboard(buttons: list, cols=1):
        pass

    @staticmethod
    def get_mention(user, name=None):
        pass

    def delete_message(self, peer_id, message_id):
        pass


def get_bot_by_platform(platform: Platform):
    """
    Получение бота по платформе
    """
    from apps.bot.classes.bots.VkBot import VkBot
    from apps.bot.classes.bots.TgBot import TgBot
    # from apps.bot.classes.bots.YandexBot import YandexBot

    platforms = {
        Platform.VK: VkBot,
        Platform.TG: TgBot,
        # Platform.YANDEX: YandexBot
    }
    return platforms[platform]


def send_message_to_moderator_chat(msgs):
    def get_moderator_chat_peer_id():
        test_chat_id = env.str("TG_MODERATOR_CHAT_PK")
        return Chat.objects.get(pk=test_chat_id).chat_id

    def get_moderator_bot_class():
        from apps.bot.classes.bots.TgBot import TgBot
        return TgBot

    bot = get_moderator_bot_class()()
    peer_id = get_moderator_chat_peer_id()
    bot.parse_and_send_msgs(peer_id, msgs)


def upload_image_to_vk_server(image):
    vk_bot = get_bot_by_platform(Platform.VK)()
    photos = vk_bot.upload_photos(image, 1)
    return photos[0].public_download_url

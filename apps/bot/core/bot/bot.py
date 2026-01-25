import logging
import time
from math import inf
from threading import Lock
from threading import Thread

from django.db.models import Q

from apps.bot.consts import RoleEnum
from apps.bot.core.activities import ActivitiesEnum
from apps.bot.core.bot_response import BotResponse
from apps.bot.core.chat_activity import ChatActivity
from apps.bot.core.event.event import Event
from apps.bot.core.messages.attachments.audio import AudioAttachment
from apps.bot.core.messages.attachments.document import DocumentAttachment
from apps.bot.core.messages.attachments.gif import GifAttachment
from apps.bot.core.messages.attachments.photo import PhotoAttachment
from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.models import Profile, Chat, Bot as BotModel, User
from apps.shared.exceptions import PWarning, PError, PSkip, PIDK, PSkipContinue
from apps.shared.utils.utils import get_chunks
from petrovich.settings import env

lock = Lock()


class Bot(Thread):
    ERROR_MSG = "Непредвиденная ошибка. Сообщите разработчику."

    CODE_TAG = None
    PRE_TAG = None
    SPOILER_TAG = None
    BOLD_TAG = None
    ITALIC_TAG = None
    LINK_TAG = None
    STROKE_TAG = None
    UNDERLINE_TAG = None
    QUOTE_TAG = None

    MAX_MESSAGE_TEXT_LENGTH = inf
    MAX_VIDEO_SIZE_MB = inf

    def __init__(self, platform, **kwargs):
        Thread.__init__(self)
        self.log_filter = {}

        self.platform = platform

        self.logger = logging.getLogger('bot')

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

    # Костыль (?)
    def init_requests(self):
        pass

    def handle_event(self, event: Event, send=True) -> ResponseMessage | None:
        """
        Обработка входящего ивента
        """
        try:
            event.setup_event()
            if not event.need_a_response():
                return None

            if event.sender and not event.sender.check_role(RoleEnum.TRUSTED):
                raise PWarning("Обратитесь за доступом к создателю бота.")

            self.log_filter = event.log_filter
            self.init_requests()

            rm = self.route(event)
            # Если мы попали в команду и не вылетели по exception
            self.log_event(event)
            if not rm:
                return None
            self.log_message(rm)

        # Если предвиденная ошибка
        except (PWarning, PError) as e:
            self.log_event(event)
            rm = ResponseMessage(
                ResponseMessageItem(
                    text=e.msg,
                    peer_id=event.peer_id,
                    message_thread_id=event.message_thread_id,
                    reply_to=e.reply_to,
                    keyboard=e.keyboard
                )
            )
            self.log_message(rm, e.level)
        # Если нужно пропустить
        except (PSkip, PIDK):
            return None
        # Непредвиденная ошибка
        except Exception:
            self.log_event(event)
            rmi = ResponseMessageItem(
                text=f"{self.ERROR_MSG}\nКоманда {self.get_formatted_text_line('/баг')}",
                peer_id=event.peer_id,
                message_thread_id=event.message_thread_id,
            )
            if event.sender and event.sender.check_role(RoleEnum.TRUSTED):
                button = self.get_button('Логи', command="логи")
                keyboard = self.get_inline_keyboard([button])
                rmi.keyboard = keyboard
            rm = ResponseMessage(rmi)
            self.log_message(rm, "exception")
        # finally:
        #     if rm:
        #         self.stop_activity_thread(rm.messages[0].peer_id)

        if rm and send and rm.send:
            self.send_response_message(rm)
        return rm

    def send_response_message(self, rm: ResponseMessage) -> list[BotResponse] | None:
        """
        Отправка ResponseMessage сообщения
        Вовзращает список результатов отправки в формате
        [{success:bool, response:Response}]
        """

        results = []

        for rmi in rm.messages:
            if not rmi.send:
                continue
            if rm.thread:
                Thread(target=self.send_response_message_item, args=(rmi,)).start()
            else:
                br = self.send_response_message_item(rmi)
                results.append(br)
            if rm.delay:
                time.sleep(rm.delay)
        return results

    def send_response_message_item(self, rmi: ResponseMessageItem) -> BotResponse:
        """
        Отправка ResponseMessageItem сообщения
        Возвращает BotResponse
        """
        raise NotImplementedError

    def route(self, event: Event) -> ResponseMessage | None:
        """
        Выбор команды
        Если в Event есть команда, поиск не требуется
        """
        from apps.commands.registry import registry_commands

        if event.command:
            return event.command().check_and_start(self, event)
        for command in registry_commands:
            if command.accept(event):
                try:
                    return command.__class__().check_and_start(self, event)
                # Гипотеза, что если мы скипаем команду, то можем идти дальше ?
                except PSkipContinue:
                    continue
        # Если это нотификация, то это ок
        if event.is_notify:
            raise PSkip()

        # Если указана настройка не реагировать на неверные команды, то скипаем
        if not event.sender.settings.need_reaction:
            raise PSkip()

        # Если указана настройка реагировать на команды без слеша, но команду мы не нашли, то скипаем
        # Но только в случае если нет явного упоминания нас, тогда точно даём ответ
        if event.chat and event.chat.settings.no_mention and event.message and not event.message.mentioned:
            raise PSkip()

        if not event.message or not event.message.raw:
            # ToDo: ignore?
            answer = "Я не понял, что вы от меня хотите(("
        else:
            answer = f"Я не понял команды \"{event.message.command}\"\n"

        rm = ResponseMessage(
            ResponseMessageItem(
                text=answer,
                peer_id=event.peer_id,
                message_thread_id=event.message_thread_id
            ))
        return rm

    # END MAIN ROUTING AND MESSAGING

    # LOGGING

    def log_event(self, event: Event):
        log_data = {"event": event.to_log()}
        if self.log_filter:
            log_data.update({'log_filter': self.log_filter})
        self.logger.debug(log_data)

    def log_message(self, message, level="debug"):
        log_data = {"message": message.to_log()}
        if self.log_filter:
            log_data.update({'log_filter': self.log_filter})
        getattr(self.logger, level)(log_data)

    # END LOGGING

    # USERS GROUPS BOTS

    def get_user_by_id(self, user_id, _defaults: dict = None) -> User:
        """
        Получение пользователя по его id
        """
        if not _defaults:
            _defaults = {}
        defaults = {}
        defaults.update(_defaults)

        with lock:
            user, _ = User.objects.get_or_create(
                user_id=user_id,
                platform=self.platform.name,
                defaults=defaults
            )
        return user

    def get_profile_by_user_id(self, user_id):
        user = self.get_user_by_id(user_id)
        profile = self.get_profile_by_user(user)
        return profile

    @staticmethod
    def get_profile_by_user(user: User, _defaults: dict = None) -> Profile:
        """
        Возвращает профиль по пользователю
        """
        if not _defaults:
            _defaults = {}
        defaults = {}
        defaults.update(_defaults)

        if not user.profile:
            with lock:
                profile = Profile(**defaults)
                profile.save()
                user.profile = profile
                user.save()

        return user.profile

    @staticmethod
    def get_profile_by_name(filters: list, filter_chat=None) -> Profile:
        """
        Получение пользователя по имени/фамилии/имени и фамилии/никнейма/ид
        """
        users = Profile.objects.all()
        if filter_chat:
            users = users.filter(chats=filter_chat)

        for _filter in filters:
            q = Q(name__icontains=_filter) | Q(surname__icontains=_filter) | Q(nickname_real__icontains=_filter)
            users = users.filter(q)

        if len(users) == 0:
            filters_str = " ".join(filters)
            raise PWarning(f"Пользователь {filters_str} не найден. Возможно опечатка или он мне ещё ни разу не писал")
        elif len(users) > 1:
            raise PWarning("2 и более пользователей подходит под поиск")

        return users.first()

    def get_chat_by_id(self, chat_id: int) -> Chat:
        """
        Возвращает чат по его id
        """
        with lock:
            chat, _ = Chat.objects.get_or_create(
                chat_id=chat_id, platform=self.platform.name
            )
        return chat

    def get_bot_by_id(self, bot_id: int) -> BotModel:
        """
        Возвращает бота по его id
        """
        if bot_id > 0:
            bot_id = -bot_id
        with lock:
            bot, _ = BotModel.objects.get_or_create(
                bot_id=bot_id, platform=self.platform.name
            )
        return bot

    @staticmethod
    def add_chat_to_profile(profile: Profile, chat: Chat):
        """
        Добавление чата пользователю
        """
        with lock:
            chats = profile.chats
            if chat not in chats.all():
                chats.add(chat)

    @staticmethod
    def remove_chat_from_profile(profile: Profile, chat: Chat):
        """
        Удаление чата пользователю
        """
        with lock:
            chats = profile.chats
            if chat in chats.all():
                chats.remove(chat)

    # END USERS GROUPS BOTS

    # ATTACHMENTS
    def get_photo_attachment(
            self,
            image,
            peer_id: str | int | None = None,
            allowed_exts_url: list[str] | None = None,
            guarantee_url: bool = False,
            filename: str | None = None,
            send_chat_action: bool = True
    ) -> PhotoAttachment:
        """
        Получение фото
        """
        if allowed_exts_url is None:
            allowed_exts_url = ['jpg', 'jpeg', 'png', 'webp', 'heic']
        pa = PhotoAttachment()
        with ChatActivity(self, ActivitiesEnum.UPLOAD_PHOTO, peer_id, send_chat_action=send_chat_action):
            pa.parse(image, allowed_exts_url, guarantee_url=guarantee_url, filename=filename)
        return pa

    def get_document_attachment(
            self,
            document,
            peer_id: str | int | None = None,
            filename: str = None,
            send_chat_action: bool = True
    ) -> DocumentAttachment:
        """
        Получение документа
        """
        da = DocumentAttachment()
        with ChatActivity(self, ActivitiesEnum.UPLOAD_DOCUMENT, peer_id, send_chat_action=send_chat_action):
            da.parse(document, filename=filename)
        return da

    def get_audio_attachment(
            self,
            audio,
            peer_id: str | int | None = None,
            title: str | None = None,
            artist: str | None = None,
            filename: str | None = None,
            thumbnail: PhotoAttachment | None = None,
            thumbnail_url: str | None = None,
            send_chat_action: bool = True
    ) -> AudioAttachment:
        """
        Получение аудио
        """
        aa = AudioAttachment()
        with ChatActivity(self, ActivitiesEnum.UPLOAD_AUDIO, peer_id, send_chat_action=send_chat_action):
            aa.parse(audio, filename=filename)
        aa.thumbnail = thumbnail
        aa.thumbnail_url = thumbnail_url
        aa.title = title
        aa.artist = artist
        return aa

    def get_video_attachment(
            self,
            video,
            peer_id: str | int | None = None,
            filename: str | None = None,
            thumbnail: PhotoAttachment | None = None,
            thumbnail_url: str | None = None,
            send_chat_action: bool = True
    ) -> VideoAttachment:
        """
        Получение видео
        """
        va = VideoAttachment()
        with ChatActivity(self, ActivitiesEnum.UPLOAD_VIDEO, peer_id, send_chat_action=send_chat_action):
            va.parse(video, filename=filename)
        va.thumbnail = thumbnail
        va.thumbnail_url = thumbnail_url
        return va

    def get_gif_attachment(
            self,
            gif,
            peer_id: str | int | None = None,
            filename: str | None = None,
            send_chat_action: bool = True
    ) -> GifAttachment:
        """
        Получение гифки
        """
        ga = GifAttachment()
        with ChatActivity(self, ActivitiesEnum.UPLOAD_VIDEO, peer_id, send_chat_action=send_chat_action):
            ga.parse(gif, filename=filename)
        return ga

    # END ATTACHMENTS

    # EXTRA
    def set_activity(self, chat_id: int | str, activity: ActivitiesEnum):
        """
        Проставление активности боту (например, отправка сообщения)
        """

    # ToDo: А может лучше перенести в Event?
    @staticmethod
    def get_button(text: str, command: str = None, args: list = None, kwargs: dict = None, url: str = None):
        """
        Определение кнопки для клавиатур
        """

    def get_inline_keyboard(self, buttons: list, cols=1):
        """
        param buttons: ToDo:
        Получение инлайн-клавиатуры с кнопками
        В основном используется для команд, где нужно запускать много команд и лень набирать заново
        """
        buttons_chunks = get_chunks(buttons, cols)
        keyboard = list(buttons_chunks)
        return keyboard

    def get_mention(self, profile: Profile) -> str:
        """
        Получение меншона пользователя
        """
        return str(profile)

    def delete_messages(self, chat_id: int | str, message_ids: list[int] | int) -> dict:
        """
        Удаление сообщения
        """

    @classmethod
    def get_formatted_text(cls, text: str, language: str = None) -> str:
        """
        Форматированный текст
        """
        return text

    @classmethod
    def get_formatted_text_line(cls, text: str) -> str:
        """
        Форматированный текст в одну линию
        """
        return text

    @classmethod
    def get_formatted_url(cls, name, url) -> str:
        return url

    @classmethod
    def get_underline_text(cls, text: str) -> str:
        """
        Текст с нижним подчёркиванием
        """
        return text

    @classmethod
    def get_italic_text(cls, text: str) -> str:
        """
        Наклонный текст
        """
        return text

    @classmethod
    def get_bold_text(cls, text: str) -> str:
        """
        Жирный текст
        """
        return text

    @classmethod
    def get_strike_text(cls, text: str) -> str:
        """
        Жирный текст
        """
        return text

    @classmethod
    def get_spoiler_text(cls, text: str) -> str:
        """
        Спойлер-текст
        """
        return text

    @classmethod
    def get_quote_text(cls, text: str, expandable: bool = False) -> str:
        """
        Цитата текст
        """
        return text

    # END EXTRA

    # ToDo: куда это?
    def edit_message(self, default_params) -> dict:
        pass


def send_message_to_moderator_chat(msg: ResponseMessageItem):
    def get_moderator_chat_peer_id():
        test_chat_id = env.str("TG_MODERATOR_CHAT_PK")
        return Chat.objects.get(pk=test_chat_id).chat_id

    from apps.bot.core.bot.tg_bot.tg_bot import TgBot
    bot = TgBot()
    msg.peer_id = get_moderator_chat_peer_id()
    return bot.send_response_message_item(msg)

import logging
import threading
import time
from threading import Lock
from threading import Thread
from typing import List, Optional

from django.contrib.auth.models import Group

from apps.bot.classes.BotResponse import BotResponse
from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.consts.Exceptions import PWarning, PError, PSkip, PIDK
from apps.bot.classes.events.Event import Event
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem
from apps.bot.classes.messages.attachments.AudioAttachment import AudioAttachment
from apps.bot.classes.messages.attachments.DocumentAttachment import DocumentAttachment
from apps.bot.classes.messages.attachments.GifAttachment import GifAttachment
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.models import Profile, Chat, Bot as BotModel, User
from apps.bot.utils.utils import tanimoto, get_chunks, fix_layout, get_flat_list, has_cyrillic
from apps.games.models import Gamer
from petrovich.settings import env

lock = Lock()


class Bot(Thread):
    ERROR_MSG = "Непредвиденная ошибка. Сообщите разработчику. Команда /баг"

    def __init__(self, platform, **kwargs):
        Thread.__init__(self)

        self.platform = platform
        self.user_model = User.objects.filter(platform=self.platform.name)
        self.chat_model = Chat.objects.filter(platform=self.platform.name)
        self.bot_model = BotModel.objects.filter(platform=self.platform.name)

        self.logger = logging.getLogger('bot')

        self.activity_thread_flag = False

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

    def handle_event(self, event: Event, send=True) -> Optional[ResponseMessage]:
        """
        Обработка входящего ивента
        """
        try:
            event.setup_event()
            if not event.need_a_response():
                return
            rm = self.route(event)
            if send:
                self.send_response_message(rm)
            return rm
        except PSkip:
            pass
        except Exception:
            rm = ResponseMessage(
                ResponseMessageItem(
                    text=self.ERROR_MSG,
                    peer_id=event.peer_id,
                    message_thread_id=event.message_thread_id
                )
            )
            # exc_info = traceback.format_exc()
            self.log_message(rm, "exception")
            if send:
                self.send_response_message(rm)
            return rm
        finally:
            self.stop_activity_thread()

    def send_response_message_thread(self, rm: ResponseMessage):
        for rmi in rm.messages:
            Thread(target=self.send_response_message_item, args=(rmi,)).start()

    def send_response_message(self, rm: ResponseMessage) -> List[BotResponse]:
        """
        Отправка ResponseMessage сообщения
        Вовзращает список результатов отправки в формате
        [{success:bool, response:Response}]
        """
        results = []

        for rmi in rm.messages:
            br = self.send_response_message_item(rmi)
            results.append(br)
        return results

    def send_response_message_item(self, rmi: ResponseMessageItem) -> BotResponse:
        """
        Отправка ResponseMessageItem сообщения
        Возвращает BotResponse
        """

    def route(self, event: Event) -> Optional[ResponseMessage]:
        """
        Выбор команды
        Если в Event есть команда, поиск не требуется
        """
        from apps.bot.initial import COMMANDS

        commands = [event.command()] if event.command else COMMANDS

        for command in commands:
            try:
                if command.accept(event):
                    self.log_event(event)
                    rm = command.__class__().check_and_start(self, event)
                    if rm:
                        self.log_message(rm)
                    return rm
            except (PWarning, PError) as e:
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
                return rm
            except PIDK:
                continue
            except PSkip as e:
                raise e

        # Если указана настройка не реагировать на неверные команды, то скипаем
        if event.chat and not event.chat.need_reaction:
            raise PSkip()

        # Если указана настройка реагировать на команды без слеша, но команду мы не нашли, то скипаем
        # Но только в случае если нет явного упоминания нас, тогда точно даём ответ
        if event.chat and event.chat.mentioning and event.message and not event.message.mentioned:
            raise PSkip()

        similar_command, keyboard = self.get_similar_command(event, COMMANDS)
        rm = ResponseMessage(
            ResponseMessageItem(
                text=similar_command,
                keyboard=keyboard,
                peer_id=event.peer_id,
                message_thread_id=event.message_thread_id
            ))
        self.log_message(rm)
        return rm

    def get_similar_command(self, event: Event, commands):
        """
        Получение похожей команды по неправильно введённой
        """
        user_groups = event.sender.get_list_of_role_names()
        if not event.message or not event.message.raw:
            idk_what_you_want = "Я не понял, что вы от меня хотите(("
            return idk_what_you_want, {}
        original_text = event.message.raw.split(' ')
        messages = [original_text[0]]

        # Если в тексте нет кириллицы, то предлагаем пофикшенное название команды
        if not has_cyrillic(original_text[0]):
            fixed_command = fix_layout(original_text[0])
            messages.append(fixed_command)
        tanimoto_commands = [{command: 0 for command in commands} for _ in range(len(messages))]

        for command in commands:
            command_has_not_full_names = not command.full_names
            user_has_not_access = command.access.name not in user_groups
            command_is_not_suggested = not command.suggest_for_similar

            if command_has_not_full_names or user_has_not_access or command_is_not_suggested:
                continue

            for name in command.full_names:
                if name:
                    for i, message in enumerate(messages):
                        tanimoto_commands[i][command] = max(tanimoto(message, name), tanimoto_commands[i][command])

        # Сортируем словари, берём топ2 и делаем из них один список, который повторно сортируем
        tanimoto_commands = [{k: v for k, v in sorted(x.items(), key=lambda item: item[1], reverse=True)} for x in
                             tanimoto_commands]
        tanimoto_commands = get_flat_list([list(x.items())[:2] for x in tanimoto_commands])
        tanimoto_commands = sorted(tanimoto_commands, key=lambda x: x[1], reverse=True)

        msg = f"Я не понял команды \"{event.message.command}\"\n"
        if tanimoto_commands[0][0] and tanimoto_commands[0][1] != 0:
            msg += f"Возможно вы имели в виду команду \"{tanimoto_commands[0][0].name}\""
        buttons = []
        for command in tanimoto_commands:
            command_name = command[0].name
            # Добавляем в клаву просто команду
            buttons.append(self.get_button(command_name, command_name))
        keyboard = {}
        if buttons:
            keyboard = self.get_inline_keyboard(buttons, 1)
        return msg, keyboard

    # END MAIN ROUTING AND MESSAGING

    # LOGGING

    def log_event(self, event: Event):
        self.logger.debug({"event": event.to_log()})

    def log_message(self, message, level="debug"):
        getattr(self.logger, level)({"message": message.to_log()})

    def log_response(self, response: dict, action):
        self.logger.debug({"response": response, "action": action})

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

    @staticmethod
    def get_profile_by_user(user: User, is_new=False, _defaults: dict = None) -> Profile:
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
                is_new = True

        if is_new:
            with lock:
                user.profile.save()

                group_user = Group.objects.get(name=Role.USER.name)
                group_gamer = Group.objects.get(name=Role.GAMER.name)
                user.profile.groups.add(group_user)
                user.profile.groups.add(group_gamer)
        return user.profile

    # ToDo: очень говнокод
    # ToDo: capitalize
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
            if not user:
                user = users.filter(name=args[1].capitalize(), surname=args[0].capitalize())

        else:
            user = users.filter(nickname_real=args[0].capitalize())
            if len(user) == 0:
                user = users.filter(name=args[0].capitalize())
                if len(user) == 0:
                    user = users.filter(surname=args[0].capitalize())

        if len(user) > 1:
            raise PWarning("2 и более пользователей подходит под поиск")

        if len(user) == 0:
            args_str = " ".join(args)
            raise PWarning(f"Пользователь {args_str} не найден. Возможно опечатка или он мне ещё ни разу не писал")

        return user.first()

    def get_chat_by_id(self, chat_id: int) -> Chat:
        """
        Возвращает чат по его id
        """
        with lock:
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
        with lock:
            bot, _ = self.bot_model.get_or_create(
                bot_id=bot_id, platform=self.platform.name
            )
        return bot

    @staticmethod
    def get_gamer_by_profile(profile: Profile) -> Gamer:
        """
        Получение игрока по модели пользователя
        """
        with lock:
            gamer, _ = Gamer.objects.get_or_create(profile=profile)
        return gamer

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
    def get_photo_attachment(self, image, peer_id=None, allowed_exts_url=None, guarantee_url=False, filename=None):
        """
        Получение фото
        """
        if allowed_exts_url is None:
            allowed_exts_url = ['jpg', 'jpeg', 'png']
        if peer_id:
            self.set_activity_thread(peer_id, ActivitiesEnum.UPLOAD_PHOTO)
        pa = PhotoAttachment()
        pa.parse(image, allowed_exts_url, guarantee_url=guarantee_url, filename=filename)
        self.stop_activity_thread()
        return pa

    def get_document_attachment(self, document, peer_id=None, filename=None):
        """
        Получение документа
        """
        if peer_id:
            self.set_activity_thread(peer_id, ActivitiesEnum.UPLOAD_DOCUMENT)
        da = DocumentAttachment()
        da.parse(document, filename=filename)
        self.stop_activity_thread()
        return da

    def get_audio_attachment(self, audio, peer_id=None, title=None, artist=None, filename=None, thumb=None):
        """
        Получение аудио
        """
        if peer_id:
            self.set_activity_thread(peer_id, ActivitiesEnum.UPLOAD_AUDIO)
        va = AudioAttachment()
        va.parse(audio, filename=filename)
        va.thumb = thumb
        va.title = title
        va.artist = artist
        self.stop_activity_thread()
        return va

    def get_video_attachment(self, document, peer_id=None, filename=None):
        """
        Получение видео
        """
        if peer_id:
            self.set_activity_thread(peer_id, ActivitiesEnum.UPLOAD_VIDEO)
        va = VideoAttachment()
        va.parse(document, filename=filename)
        self.stop_activity_thread()
        return va

    def get_gif_attachment(self, gif, peer_id=None, filename=None):
        """
        Получение гифки
        """
        if peer_id:
            self.set_activity_thread(peer_id, ActivitiesEnum.UPLOAD_VIDEO)
        ga = GifAttachment()
        ga.parse(gif, filename=filename)
        self.stop_activity_thread()
        return ga

    # END ATTACHMENTS

    # EXTRA
    def set_activity(self, peer_id, activity: ActivitiesEnum):
        """
        Проставление активности боту (например, отправка сообщения)
        """

    def set_activity_thread(self, peer_id, activity: ActivitiesEnum):
        self.activity_thread_flag = True
        threading.Thread(
            target=self._set_activity_thread,
            args=(peer_id, activity)
        ).start()

    def stop_activity_thread(self):
        self.activity_thread_flag = False

    def _set_activity_thread(self, peer_id, activity):
        while self.activity_thread_flag:
            self.set_activity(peer_id, activity)
            time.sleep(5)

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

    def get_mention(self, profile: Profile, name=None):
        """
        Получение меншона пользователя
        """

    def delete_message(self, peer_id, message_id):
        """
        Удаление сообщения
        """

    @classmethod
    def get_formatted_text(cls, text: str) -> str:
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

    # END EXTRA


def send_message_to_moderator_chat(msg: ResponseMessageItem):
    def get_moderator_chat_peer_id():
        test_chat_id = env.str("TG_MODERATOR_CHAT_PK")
        return Chat.objects.get(pk=test_chat_id).chat_id

    from apps.bot.classes.bots.tg.TgBot import TgBot
    bot = TgBot()
    msg.peer_id = get_moderator_chat_peer_id()
    return bot.send_response_message_item(msg)

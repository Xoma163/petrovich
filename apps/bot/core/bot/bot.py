import logging
from io import BytesIO
from math import inf
from threading import Lock

from apps.bot.consts import RoleEnum
from apps.bot.core.bot_response import BotResponse
from apps.bot.core.chat_action_sender import ChatActionSender
from apps.bot.core.chat_actions import ChatActionEnum
from apps.bot.core.event.event import Event
from apps.bot.core.messages.attachments.audio import AudioAttachment
from apps.bot.core.messages.attachments.document import DocumentAttachment
from apps.bot.core.messages.attachments.gif import GifAttachment
from apps.bot.core.messages.attachments.photo import PhotoAttachment
from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.models import Profile
from apps.shared.exceptions import PWarning, PError, PSkip, PIDK, PSkipContinue

lock = Lock()


class Bot:
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
        self.log_filter = {}

        self.platform = platform

        self.logger = logging.getLogger('bot')

    # MAIN ROUTING AND MESSAGING

    def run(self):
        """
        Thread запуск основного тела команды
        """

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
            br = self.send_response_message_item(rmi)
            results.append(br)
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

    # ATTACHMENTS
    # Куда это можно унести? И нужно ли? Технически можно если отказаться от with ChatAction именно здесь
    def get_photo_attachment(
            self,
            url: str | None = None,
            path: str | None = None,
            _bytes: bytes | BytesIO | None = None,
            filename: str | None = None,

            peer_id: str | int | None = None,
            send_chat_action: bool = True,
    ) -> PhotoAttachment:
        """
        Получение фото
        """
        pa = PhotoAttachment()
        with ChatActionSender(self, ChatActionEnum.UPLOAD_PHOTO, peer_id, send_chat_action=send_chat_action):
            pa.parse(url, path, _bytes, filename=filename)
        return pa

    def get_document_attachment(
            self,
            url: str | None = None,
            path: str | None = None,
            _bytes: bytes | BytesIO | None = None,
            filename: str | None = None,

            peer_id: str | int | None = None,
            send_chat_action: bool = True,

            thumbnail_bytes: bytes | None = None,
            thumbnail_url: str | None = None,
    ) -> DocumentAttachment:
        """
        Получение документа
        """
        da = DocumentAttachment()
        with ChatActionSender(self, ChatActionEnum.UPLOAD_DOCUMENT, peer_id, send_chat_action=send_chat_action):
            da.parse(url, path, _bytes, filename=filename)

        da.thumbnail_bytes = thumbnail_bytes
        da.thumbnail_url = thumbnail_url

        return da

    def get_audio_attachment(
            self,
            url: str | None = None,
            path: str | None = None,
            _bytes: bytes | BytesIO | None = None,
            filename: str | None = None,

            peer_id: str | int | None = None,
            send_chat_action: bool = True,

            title: str | None = None,
            artist: str | None = None,
            thumbnail_bytes: bytes | None = None,
            thumbnail_url: str | None = None,
    ) -> AudioAttachment:
        """
        Получение аудио
        """
        aa = AudioAttachment()
        with ChatActionSender(self, ChatActionEnum.UPLOAD_AUDIO, peer_id, send_chat_action=send_chat_action):
            aa.parse(url, path, _bytes, filename=filename)

        aa.thumbnail_bytes = thumbnail_bytes
        aa.thumbnail_url = thumbnail_url
        aa.title = title
        aa.artist = artist
        return aa

    def get_video_attachment(
            self,
            url: str | None = None,
            path: str | None = None,
            _bytes: bytes | BytesIO | None = None,
            filename: str | None = None,

            peer_id: str | int | None = None,
            send_chat_action: bool = True,

            width: int | None = None,
            height: int | None = None,
            thumbnail_bytes: bytes | None = None,
            thumbnail_url: str | None = None,
    ) -> VideoAttachment:
        """
        Получение видео
        """
        va = VideoAttachment()
        with ChatActionSender(self, ChatActionEnum.UPLOAD_VIDEO, peer_id, send_chat_action=send_chat_action):
            va.parse(url, path, _bytes, filename=filename)
        va.width = width
        va.height = height
        va.thumbnail_bytes = thumbnail_bytes
        va.thumbnail_url = thumbnail_url
        return va

    def get_gif_attachment(
            self,
            url: str | None = None,
            path: str | None = None,
            _bytes: bytes | BytesIO | None = None,
            filename: str | None = None,

            peer_id: str | int | None = None,
            send_chat_action: bool = True,
    ) -> GifAttachment:
        """
        Получение гифки
        """
        ga = GifAttachment()
        with ChatActionSender(self, ChatActionEnum.UPLOAD_VIDEO, peer_id, send_chat_action=send_chat_action):
            ga.parse(url, path, _bytes, filename=filename)
        return ga

    # END ATTACHMENTS

    # EXTRA
    def set_chat_action(self, chat_id: int | str, chat_action: ChatActionEnum):
        """
        Проставление активности боту (например, отправка сообщения)
        """

    @staticmethod
    def get_button(text: str, command: str = None, args: list = None, kwargs: dict = None, url: str = None):
        """
        Определение кнопки для клавиатур
        """

    @staticmethod
    def get_inline_keyboard(buttons: list, cols=1):
        """
        param buttons: ToDo:
        Получение инлайн-клавиатуры с кнопками
        В основном используется для команд, где нужно запускать много команд и лень набирать заново
        """

    def get_mention(self, profile: Profile) -> str:
        """
        Получение меншона пользователя
        """
        return str(profile)

    def delete_messages(self, chat_id: int | str, message_ids: list[int] | int) -> dict:
        """
        Удаление сообщения
        """

    def edit_message(self, default_params) -> dict:
        """
        Редактирование сообщения
        """

    # ToDo думаю это надо куда-то унести

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

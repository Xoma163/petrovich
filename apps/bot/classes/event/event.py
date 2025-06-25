import copy

from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.messages.attachments.attachment import Attachment
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.document import DocumentAttachment
from apps.bot.classes.messages.attachments.gif import GifAttachment
from apps.bot.classes.messages.attachments.link import LinkAttachment
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.attachments.sticker import StickerAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.classes.messages.attachments.video_note import VideoNoteAttachment
from apps.bot.classes.messages.attachments.voice import VoiceAttachment
from apps.bot.classes.messages.message import Message
from apps.bot.models import Profile, Chat, User
from apps.bot.utils.cache import MessagesCache


class Event:
    # None тк иногда требуется вручную создать инстанс Event
    def __init__(self, raw_event=None, use_db=True):
        from apps.bot.classes.command import Command

        if not raw_event:
            raw_event = {}
        self.bot = None
        self.raw: dict = raw_event  # json
        self.use_db: bool = use_db

        self.is_from_user: bool = False
        self.is_from_bot: bool = False
        self.is_from_bot_me: bool = False  # Сообщение от этого бота
        self.is_from_chat: bool = False
        self.is_from_pm: bool = False

        self.user_id: int | None = None
        self.user: User | None = None
        self.sender: Profile | None = None

        self.chat_id: int | None = None
        self.chat: Chat | None = None
        self.peer_id: int | None = None  # Куда слать ответ
        self.from_id: int | None = None  # От кого пришло сообщение
        self.platform: Platform | None = None

        self.payload: dict = {}
        self.action: dict = {}

        self.message: Message | None = None
        self.fwd: list = []
        self.attachments: list = []

        self.force_response: bool | None = None
        self.command: Command | None = None

        self.is_fwd: bool = False

        # Если это crontab notifier
        self.is_notify: bool = False

        # Tg
        self.message_thread_id: int | None = None

    def setup_event(self, **kwargs):
        """
        Метод по установке ивента у каждого бота. Переопределяется всегда
        """
        if self.use_db:
            self._cache()

    def need_a_response(self):
        """
        Проверка, нужен ли пользователю ответ
        """
        if self.force_response is not None:
            return self.force_response
        if self.action:
            return True
        if not self.sender:
            return False

        if self.sender.check_role(Role.BANNED):
            return False
        if self.is_from_bot:
            return False
        if self.payload:
            return True

        need_a_response_extra = self.need_a_response_extra()
        if need_a_response_extra:
            return True

        if self.is_from_pm:
            return True

        if self.message is None:
            return False

        if self.chat and self.chat.settings.no_mention:
            return True

        if self.is_from_chat and not self.message.mentioned:
            return False

        if self.message.mentioned:
            return True

        return False

    def need_a_response_extra(self):
        """
        Проверка, нужен ли пользователю ответ c учётом особенностей команд
        """
        from apps.bot.initial import EXTRA_COMMANDS

        for e_command in EXTRA_COMMANDS:
            if e_command.accept_extra(self):
                self.command = e_command.__class__
                return True

        return False

    @property
    def has_voice_message(self):
        """
        Есть ли голосовое сообщение во вложениях
        """
        return self.has_attachment(VoiceAttachment)

    @property
    def has_video_note(self):
        """
        Есть ли кружочек во вложениях
        """
        return self.has_attachment(VideoNoteAttachment)

    def has_attachment(self, attachment_type: type[Attachment]):
        for att in self.attachments:
            if isinstance(att, attachment_type):
                return True
        return False

    def set_message(self, text, _id=None):
        """
        Проставление сообщения
        """
        self.message = Message(text, _id) if text else None

    def get_all_attachments(self, types: list | None = None, use_fwd=True):
        if types is None:
            types = [
                AudioAttachment, DocumentAttachment, GifAttachment, LinkAttachment,
                PhotoAttachment, StickerAttachment, VideoAttachment, VideoNoteAttachment
            ]
        attachments = []
        if self.attachments:
            attachments = [att for att in self.attachments if isinstance(att, tuple(types))]

        if use_fwd and self.fwd:
            attachments_fwd = [att for msg in self.fwd for att in msg.attachments if isinstance(att, tuple(types))]
            attachments.extend(attachments_fwd)

        return attachments

    def to_log(self) -> dict:
        """
        Подготовка ивента к логированию
        """
        dict_self = copy.copy(self.__dict__)
        ignore_fields = ['bot']
        for ignore_field in ignore_fields:
            del dict_self[ignore_field]
        dict_self['message'] = dict_self['message'].to_log() if dict_self['message'] else {}
        dict_self['fwd'] = [x.to_log() for x in dict_self['fwd']]
        dict_self['attachments'] = [x.to_log() for x in dict_self['attachments']]

        if dict_self['command']:
            dict_self['command'] = dict_self['command'].name
        return dict_self

    def _cache(self):
        mc = MessagesCache(self.peer_id)
        mc.add_message(self.message.id, self.raw.get('message', self.raw))

    @property
    def log_filter(self) -> dict:
        return {
            'user_id': self.user.user_id if self.user else None,
            'chat_id': self.chat.chat_id if self.chat else None,
            'message_id': self.message.id if self.message else None
        }

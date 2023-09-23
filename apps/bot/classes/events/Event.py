import copy
from typing import Optional

from apps.bot.classes.consts.Consts import Platform, Role
from apps.bot.classes.messages.Message import Message
from apps.bot.classes.messages.attachments.AudioAttachment import AudioAttachment
from apps.bot.classes.messages.attachments.DocumentAttachment import DocumentAttachment
from apps.bot.classes.messages.attachments.GifAttachment import GifAttachment
from apps.bot.classes.messages.attachments.LinkAttachment import LinkAttachment
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.StickerAttachment import StickerAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.classes.messages.attachments.VideoNoteAttachment import VideoNoteAttachment
from apps.bot.classes.messages.attachments.VoiceAttachment import VoiceAttachment
from apps.bot.models import Profile, Chat, User


class Event:
    # None тк иногда требуется вручную создать инстанс Event
    def __init__(self, raw_event=None, bot=None, peer_id=None):
        from apps.bot.classes.Command import Command

        if not raw_event:
            raw_event = {}
        self.raw = raw_event  # json
        self.bot = bot

        self.is_from_user: bool = False
        self.is_from_bot: bool = False
        self.is_from_chat: bool = False
        self.is_from_pm: bool = False

        self.user: Optional[User] = None
        self.sender: Optional[Profile] = None

        self.chat: Optional[Chat] = None
        self.peer_id: int = peer_id  # Куда слать ответ
        self.from_id: Optional[int] = None  # От кого пришло сообщение
        self.platform: Platform = bot.platform

        self.payload: dict = {}
        self.action: dict = {}

        self.message: Optional[Message] = None
        self.fwd: list = []
        self.attachments: list = []

        self.force_response: Optional[bool] = None
        self.command: Optional[Command] = None

        self.is_fwd: bool = False

        # Tg
        self.message_thread_id: Optional[int] = None

    def setup_event(self, is_fwd=False):
        """
        Метод по установке ивента у каждого бота. Переопределяется всегда
        """

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

        if self.chat and self.chat.mentioning:
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
        from apps.bot.commands.Tag import Tag
        from apps.bot.commands.Meme import Meme as MemeCommand
        from apps.bot.commands.TrustedCommands.Media import Media
        from apps.bot.commands.VoiceRecognition import VoiceRecognition

        # ToDo: get automatically
        extra_commands = [Tag, MemeCommand, Media, VoiceRecognition]

        for e_command in extra_commands:
            if e_command.accept_extra(self):
                self.command = e_command
                return True

        return False

    @property
    def has_voice_message(self):
        """
        Есть ли голосовое сообщение во вложениях
        """
        for att in self.attachments:
            if isinstance(att, VoiceAttachment):
                return True
        return False

    def set_message(self, text, _id=None):
        """
        Проставление сообщения
        """
        self.message = Message(text, _id) if text else None

    def get_all_attachments(self, _type):
        attachments = []

        if _type is None:
            _type = [AudioAttachment, DocumentAttachment, GifAttachment, LinkAttachment, PhotoAttachment,
                     StickerAttachment, VideoAttachment, VideoNoteAttachment]
        if not isinstance(_type, list):
            _type = [_type]
        if self.attachments:
            for att in self.attachments:
                if type(att) in _type:
                    attachments.append(att)
        if self.fwd:
            msgs = self.fwd
            for msg in msgs:
                if msg.attachments:
                    for att in msg.attachments:
                        if type(att) in _type:
                            attachments.append(att)
        return attachments

    def to_log(self) -> dict:
        """
        Подготовка ивента к логированию
        """
        dict_self = copy.copy(self.__dict__)
        ignore_fields = ['raw', 'bot']
        for ignore_field in ignore_fields:
            del dict_self[ignore_field]
        dict_self['message'] = dict_self['message'].to_log() if dict_self['message'] else {}
        dict_self['fwd'] = [x.to_log() for x in dict_self['fwd']]
        dict_self['attachments'] = [x.to_log() for x in dict_self['attachments']]

        if dict_self['command']:
            dict_self['command'] = dict_self['command'].name
        return dict_self

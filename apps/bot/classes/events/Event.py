import copy
from urllib.parse import urlparse

from apps.bot.classes.consts.Consts import Platform, Role
from apps.bot.classes.messages.Message import Message
from apps.bot.classes.messages.attachments.DocumentAttachment import DocumentAttachment
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.classes.messages.attachments.VoiceAttachment import VoiceAttachment
from apps.bot.models import Users, Chat
from apps.bot.utils.utils import get_urls_from_text


class Event:
    # None тк иногда требуется вручную создать инстанс Event
    def __init__(self, raw_event=None, bot=None):
        from apps.bot.classes.Command import Command

        if not raw_event:
            raw_event = {}
        self.raw = raw_event  # json
        self.bot = bot

        self.is_from_user: bool = False
        self.is_from_bot: bool = False
        self.is_from_chat: bool = False
        self.is_from_pm: bool = False

        self.sender: Users = None
        self.chat: Chat = None
        self.peer_id: int = None  # Куда слать ответ
        self.from_id: int = None  # От кого пришло сообщение
        self.platform: Platform = bot.platform

        self.payload: dict = {}
        self.action = None

        self.message: Message = None
        self.fwd: list = []
        self.attachments: list = []

        self.force_need_a_response: bool = False
        self.force_not_need_a_response: bool = False
        self.command: Command = None

    def setup_event(self, is_fwd=False):
        """
        Метод по установке ивента у каждого бота. Переопределяется всегда
        """
        pass

    def need_a_response(self):
        """
        Проверка, нужен ли пользователю ответ
        """
        if self.force_not_need_a_response:
            return False

        if self.action:
            return True

        if self.sender.check_role(Role.BANNED):
            return False
        if self.is_from_bot:
            return False
        if self.force_need_a_response:
            return True

        if self.payload:
            return True

        need_a_response_extra = self.need_a_response_extra()
        if need_a_response_extra:
            return True
        if self.message is None:
            return False
        if self.is_from_pm:
            return True
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
        if self.message and not self.message.mentioned:
            if self.is_from_chat and self.chat.need_meme and not self.message.mentioned:
                from apps.bot.commands.Meme import Meme as MemeCommand
                from apps.service.models import Meme as MemeModel
                message_is_exact_meme_name = MemeModel.objects.filter(name=self.message.clear, approved=True).exists()
                if message_is_exact_meme_name:
                    self.command = MemeCommand
                    return True

            all_urls = get_urls_from_text(self.message.clear_case)
            has_fwd_with_message = self.fwd and self.fwd[0].message and self.fwd[0].message.clear_case
            if self.is_from_pm and has_fwd_with_message:
                all_urls += get_urls_from_text(self.fwd[0].message.clear_case)
            from apps.bot.commands.TrustedCommands.Media import Media
            from apps.bot.commands.TrustedCommands.Media import MEDIA_URLS
            for url in all_urls:
                message_is_media_link = urlparse(url).hostname in MEDIA_URLS
                if message_is_media_link:
                    self.command = Media
                    return True

            if self.is_from_chat and self.message.command == "@all":
                from apps.bot.commands.All import All
                self.command = All
                return True

        is_chat_auto_voice_recognize = self.is_from_chat and self.chat.recognize_voice
        if is_chat_auto_voice_recognize and self.has_voice_message:
            from apps.bot.commands.VoiceRecognition import VoiceRecognition
            self.command = VoiceRecognition
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

    def get_all_attachments(self, _type, from_first_fwd=True):
        attachments = []

        if _type is None:
            _type = [VoiceAttachment, VideoAttachment, PhotoAttachment, DocumentAttachment]
        if not isinstance(_type, list):
            _type = [_type]
        if self.attachments:
            for att in self.attachments:
                if type(att) in _type:
                    attachments.append(att)
        if self.fwd:
            if from_first_fwd:
                msgs = [self.fwd[0]]
            else:
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
        return dict_self

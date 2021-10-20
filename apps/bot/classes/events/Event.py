import copy
from urllib.parse import urlparse

from apps.bot.classes.consts.Consts import Platform, Role
from apps.bot.classes.messages.Message import Message
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
        self.command: Command = None

    def setup_event(self, is_fwd=False):
        pass

    # ToDo нужен ли ответ если чат может работать без палок
    def need_a_response(self):
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

        if self.chat and self.chat.mentioning:
            return True

        need_a_response_extra = self.need_a_response_extra()
        if need_a_response_extra:
            return True
        if self.is_from_pm:
            return True
        if self.message is None:
            return False
        if self.is_from_chat and not self.message.has_command_symbols:
            return False

        if self.message.has_command_symbols:
            return True

        return False

    def need_a_response_extra(self):
        if self.message:
            from apps.bot.commands.Meme import Meme as MemeCommand
            from apps.service.models import Meme as MemeModel
            if self.is_from_chat and self.chat.need_meme and not self.message.has_command_symbols:
                message_is_exact_meme_name = MemeModel.objects.filter(name=self.message.clear).exists()
                if message_is_exact_meme_name:
                    self.command = MemeCommand
                    return True

            from apps.bot.commands.TrustedCommands.Media import Media
            from apps.bot.commands.TrustedCommands.Media import MEDIA_URLS
            all_urls = get_urls_from_text(self.message.clear_case)
            has_fwd_with_message = self.fwd and self.fwd[0].message and self.fwd[0].message.clear_case
            if has_fwd_with_message:
                all_urls += get_urls_from_text(self.fwd[0].message.clear_case)
            for url in all_urls:
                message_is_media_link = urlparse(url).hostname in MEDIA_URLS
                if message_is_media_link:
                    self.command = Media
                    return True
        if self.is_from_chat and self.chat.recognize_voice:
            if self.has_voice_message:
                from apps.bot.commands.VoiceRecognition import VoiceRecognition
                self.command = VoiceRecognition
                return True

        return False

    @property
    def has_voice_message(self):
        for att in self.attachments:
            if isinstance(att, VoiceAttachment):
                return True
        return False

    def set_message(self, text, _id=None):
        self.message = Message(text, _id) if text else None

    def to_log(self) -> dict:
        dict_self = copy.copy(self.__dict__)
        ignore_fields = ['raw', 'bot']
        for ignore_field in ignore_fields:
            del dict_self[ignore_field]
        dict_self['message'] = dict_self['message'].to_log() if dict_self['message'] else {}
        dict_self['fwd'] = [x.to_log() for x in dict_self['fwd']]
        dict_self['attachments'] = [x.to_log() for x in dict_self['attachments']]
        return dict_self

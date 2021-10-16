from urllib.parse import urlparse

from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.messages.Message import Message
from apps.bot.classes.messages.attachments.VoiceAttachment import VoiceAttachment
from apps.bot.models import Users, Chat


class Event:
    # None тк иногда требуется вручную создать инстанс Event
    def __init__(self, raw_event=None, bot=None):
        if not raw_event:
            raw_event = {}
        self.raw = raw_event  # json
        self.bot = bot

        self.is_from_user: bool = False
        self.is_from_bot: bool = False
        self.is_from_chat: bool = False

        self.is_mentioned: bool = False

        self.sender: Users = None
        self.chat: Chat = None
        self.peer_id: str = None
        self.platform: Platform = bot.platform

        self.payload: dict = {}
        self.action = None

        self.message: Message = None
        self.fwd: list = []
        self.attachments: list = []

        self.force_need_a_response: bool = False

    def setup_event(self, is_fwd=False):
        raise NotImplementedError

    # ToDo: проверка на забаненых
    def need_a_response(self):
        if self.force_need_a_response:
            return True

        if self.is_from_bot:
            return False
        if self.has_voice_message:
            return True
        if self.message is None:
            return False
        if self.is_from_user:
            return True
        if self.payload:
            return True

        need_a_response_extra = self.need_a_response_extra()
        if need_a_response_extra:
            return True

        if self.is_from_chat and not self.message.has_command_symbols:
            return False
        return True

    def need_a_response_extra(self):
        from apps.service.models import Meme
        from apps.bot.commands.TrustedCommands.Media import MEDIA_URLS

        message_is_exact_meme_name = Meme.objects.filter(name__unaccent=self.message.clear.lower()).exists()
        if message_is_exact_meme_name:
            return True

        if self.chat and self.chat.mentioning:
            return True

        message_is_media_link = urlparse(self.message.clear).hostname in MEDIA_URLS or \
                                (self.fwd and self.fwd[0].message.clear and urlparse(self.fwd[0].message.clear) in MEDIA_URLS)
        if message_is_media_link:
            return True

    @property
    def has_voice_message(self):
        for att in self.attachments:
            if isinstance(att, VoiceAttachment):
                return True
        return False

from enum import Enum

from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.document import DocumentAttachment
from apps.bot.classes.messages.attachments.gif import GifAttachment
from apps.bot.classes.messages.attachments.link import LinkAttachment
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.attachments.sticker import StickerAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.classes.messages.attachments.video_note import VideoNoteAttachment
from apps.bot.classes.messages.attachments.voice import VoiceAttachment


class Role(Enum):
    ADMIN = "администратор"
    MODERATOR = "модератор"
    MINECRAFT = "майнкрафт"
    USER = "пользователь"
    BANNED = "забанен"
    TRUSTED = "доверенный"
    MRAZ = "мразь"
    FLAIVA = "флейва"

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    def __str__(self):
        return self.value


class Platform(Enum):
    TG = 'tg'
    API = 'api'

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)


rus_alphabet = "ёйцукенгшщзхъфывапролджэячсмитьбю"

ATTACHMENT_TYPE_TRANSLATOR = {
    'photo': PhotoAttachment,
    'video': VideoAttachment,
    'video_note': VideoNoteAttachment,
    'audio': AudioAttachment,
    'doc': DocumentAttachment,
    'link': LinkAttachment,
    'sticker': StickerAttachment,
    'voice': VoiceAttachment,
    'gif': GifAttachment
}

from enum import StrEnum

from apps.bot.core.messages.attachments.audio import AudioAttachment
from apps.bot.core.messages.attachments.document import DocumentAttachment
from apps.bot.core.messages.attachments.gif import GifAttachment
from apps.bot.core.messages.attachments.link import LinkAttachment
from apps.bot.core.messages.attachments.photo import PhotoAttachment
from apps.bot.core.messages.attachments.sticker import StickerAttachment
from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.bot.core.messages.attachments.video_note import VideoNoteAttachment
from apps.bot.core.messages.attachments.voice import VoiceAttachment


class RoleEnum(StrEnum):
    ADMIN = "администратор"
    MODERATOR = "модератор"
    MINECRAFT = "майнкрафт"
    USER = "пользователь"
    BANNED = "забанен"
    TRUSTED = "доверенный"

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    def __str__(self):
        return self.value


class PlatformEnum(StrEnum):
    TG = 'tg'

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)



ATTACHMENT_TYPE_TRANSLATOR = {
    'photo': PhotoAttachment,
    'video': VideoAttachment,
    'video_note': VideoNoteAttachment,
    'audio': AudioAttachment,
    'doc': DocumentAttachment,
    'link': LinkAttachment,
    'sticker': StickerAttachment,
    'voice': VoiceAttachment,
    # ToDo: в чём разница между gif и animation. Animation - свежее как будто?
    'gif': GifAttachment,
    'animation': GifAttachment
}

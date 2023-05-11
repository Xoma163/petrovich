from enum import Enum

from apps.bot.classes.messages.attachments.AudioAttachment import AudioAttachment
from apps.bot.classes.messages.attachments.DocumentAttachment import DocumentAttachment
from apps.bot.classes.messages.attachments.GifAttachment import GifAttachment
from apps.bot.classes.messages.attachments.LinkAttachment import LinkAttachment
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.StickerAttachment import StickerAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.classes.messages.attachments.VideoNoteAttachment import VideoNoteAttachment
from apps.bot.classes.messages.attachments.VoiceAttachment import VoiceAttachment


class Role(Enum):
    ADMIN = "администратор"
    CONFERENCE_ADMIN = "админ конфы"
    MODERATOR = "модератор"
    MINECRAFT = "майнкрафт"
    MINECRAFT_NOTIFY = "уведомления майна"
    USER = "пользователь"
    BANNED = "забанен"
    TRUSTED = "доверенный"
    MRAZ = "мразь"
    GAMER = "игрок"
    FLAIVA = "флейва"

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


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

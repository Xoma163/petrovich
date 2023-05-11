from enum import Enum


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

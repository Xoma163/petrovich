from enum import Enum

from apps.bot.classes.messages.attachments.AudioAttachment import AudioAttachment
from apps.bot.classes.messages.attachments.DocumentAttachment import DocumentAttachment
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.StickerAttachment import StickerAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.classes.messages.attachments.VoiceAttachment import VoiceAttachment


class Role(Enum):
    ADMIN = "администратор"
    CONFERENCE_ADMIN = "админ конфы"
    MODERATOR = "модератор"
    MINECRAFT = "майнкрафт"
    TERRARIA = "террария"
    MINECRAFT_NOTIFY = "уведомления майна"
    HOME = "дом"
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
    VK = 'vk'
    TG = 'tg'
    API = 'api'
    YANDEX = 'yandex'

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)


WEEK_TRANSLATOR = {
    'понедельник': 1, 'пн': 1,
    'вторник': 2, 'вт': 2,
    'среда': 3, 'ср': 3,
    'четверг': 4, 'чт': 4,
    'пятница': 5, 'пт': 5,
    'суббота': 6, 'сб': 6,
    'воскресенье': 7, 'воскресение': 7, 'вс': 7,
}

WEEK_TRANSLATOR_REVERT = {
    1: 'понедельник',
    2: 'вторник',
    3: 'среда',
    4: 'четверг',
    5: 'пятница',
    6: 'суббота',
    7: 'воскресенье'
}

ON_OFF_TRANSLATOR = {
    'вкл': True,
    'on': True,
    '1': True,
    'true': True,
    'включить': True,
    'включи': True,
    'вруби': True,
    'подключи': True,

    'выкл': False,
    'off': False,
    '0': False,
    'false': False,
    'выключить': False,
    'выключи': False,
    'выруби': False,
    'отключи': False
}

TRUE_FALSE_TRANSLATOR = {
    True: 'вкл ✅',
    False: 'выкл ⛔'
}

WEATHER_TRANSLATOR = {
    'clear': 'Ясно ☀',
    'partly-cloudy': 'Малооблачно ⛅',
    'cloudy': 'Облачно с прояснениями 🌥',
    'overcast': 'Пасмурно ☁',
    'partly-cloudy-and-light-rain': 'Небольшой дождь 🌧',
    'partly-cloudy-and-rain': 'Дождь 🌧',
    'overcast-and-rain': 'Сильный дождь 🌧🌧',
    'overcast-thunderstorms-with-rain': 'Сильный дождь, гроза 🌩',
    'cloudy-and-light-rain': 'Небольшой дождь 🌧',
    'overcast-and-light-rain': 'Небольшой дождь 🌧',
    'cloudy-and-rain': 'Дождь 🌧',
    'overcast-and-wet-snow': 'Дождь со снегом 🌨',
    'partly-cloudy-and-light-snow': 'Небольшой снег 🌨',
    'partly-cloudy-and-snow': 'Снег 🌨',
    'overcast-and-snow': 'Снегопад 🌨',
    'cloudy-and-light-snow': 'Небольшой снег 🌨',
    'overcast-and-light-snow': 'Небольшой снег 🌨',
    'cloudy-and-snow': 'Снег 🌨'
}

WEATHER_WIND_DIRECTION_TRANSLATOR = {
    "nw": "северо-западный",
    "n": "северный",
    "ne": "северо-восточный",
    "e": "восточный",
    "se": "юго-восточный",
    "s": "южный",
    "sw": "юго-западный",
    "w": "западный",
    "c": "штиль",
}

DAY_TRANSLATOR = {
    'night': 'ночь',
    'morning': 'утро',
    'day': 'день',
    'evening': 'вечер',
}

ATTACHMENT_TRANSLATOR = {
    AudioAttachment: 'аудио',
    VideoAttachment: 'видео',
    PhotoAttachment: 'фото',
    DocumentAttachment: 'документ',
    VoiceAttachment: 'голосовое',
    StickerAttachment: 'стикер'
}

BAD_ANSWERS = [
    'как же вы меня затрахали...',
    'ты обижаешь бота?',
    'тебе заняться нечем?',
    '...',
    'о боже, опять ты',
    'тебе не стыдно?',
    'зачем ты так?',
    'что я тебе сделал?',
    'чего ты добился?']

DELTA_WEEKDAY = {
    'сегодня': 0,
    'завтра': 1,
    'послезавтра': 2,
}

TURETT_WORDS = [
    "Пошёл нахуй",
    "Пидор",
    "Бля",
    "ПИДАР",
    "ЕБЛАН",
    "МАТЬ ТВОЮ В КИНО ВОДИЛ",
    "ты не прогер",
    "А может тебе ещё и станцевать, долбоёб?",
    "отсоси потом проси",
    "Как же ты меня заебал",
    "ОТЪЕБИСЬ",
    "я тебе чё, бот ебаный?",
    "хуй, пизда из одного гнезда",
    "а на грудь тебе не насрать?"
]

eng_chars = u"~`!@#$%^&qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"
rus_chars = u"ёё!\"№;%:?йцукенгшщзхъфывапролджэячсмитьбю.ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,"
trans_table = dict(zip(eng_chars, rus_chars))
trans_table_reverse = dict(zip(rus_chars, eng_chars))

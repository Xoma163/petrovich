import io
import os
import re

import pytz
# Вероятность события в процентах
from PIL import Image, ImageDraw, ImageFont

from apps.bot.classes.Consts import Role
from petrovich.settings import STATIC_ROOT


def random_probability(probability):
    if 1 > probability > 99:
        raise RuntimeError("Вероятность события должна быть от 1 до 99")
    rand_int = get_random_int(1, 100)
    if rand_int <= probability:
        return True
    else:
        return False


# Возвращает случайное событие с указанными весами этих событий
def random_event(events, weights=None):
    import random
    if weights is None:
        return random.choice(events)
    return random.choices(events, weights=weights)[0]


# Возвращает рандомное число в заданном диапазоне. Если передан seed, то по seed
def get_random_int(val1, val2=None, seed=None):
    import random
    if not val2:
        val2 = val1
        val1 = 0
    if seed:
        random.seed(seed)
    return random.randint(val1, val2)


# Есть ли кириллица
def has_cyrillic(text):
    return bool(re.search('[а-яА-Я]', text))


# Проверить вхождение пользователя в группу
def check_user_group(user, role):
    group = user.groups.filter(name=role.name)
    return group.exists()


# Получить все группы пользователя
def get_user_groups(user):
    groups = user.groups.all().values()
    return [group['name'] for group in groups]


# Убирает временную зону у datetime
def remove_tz(datetime):
    return datetime.replace(tzinfo=None)


def localize_datetime(datetime, tz):
    tz_obj = pytz.timezone(tz)
    return pytz.utc.localize(datetime, is_dst=None).astimezone(tz_obj)


def normalize_datetime(datetime, tz):
    tz_obj = pytz.timezone(tz)
    localized_time = tz_obj.localize(datetime, is_dst=None)

    tz_utc = pytz.timezone("UTC")
    return pytz.utc.normalize(localized_time, is_dst=None).astimezone(tz_utc)  # .replace(tzinfo=None)


# Возвращает упоминание пользователя
def get_mention(user, name=None):
    if not name:
        name = user.name
    return f"[id{user.user_id}|{name}]"


# Склоняет существительное после числительного
# number - число, titles - 3 склонения.
def decl_of_num(number, titles):
    cases = [2, 0, 1, 1, 1, 2]
    if 4 < number % 100 < 20:
        return titles[2]
    elif number % 10 < 5:
        return titles[cases[number % 10]]
    else:
        return titles[cases[5]]


# Получает вложения и загружает необходимые на сервер, на которых нет прав
# Прикрепляет только фото, видео, аудио и документы.
# ToDo: придумать как обрабатывать посты или ссылки
def get_attachments_for_upload(vk_bot, attachments):
    uploaded_attachments = []
    for attachment in attachments:
        # Фото
        if attachment['type'] == 'photo':
            new_attachment = vk_bot.upload_photos(attachment['download_url'])
            uploaded_attachments.append(new_attachment[0])
        # Видео, аудио, документы
        elif 'vk_url' in attachment:
            uploaded_attachments.append(attachment['vk_url'])
    return uploaded_attachments


# Получает все вложения из сообщения и пересланного сообщения
def get_attachments_from_attachments_or_fwd(vk_event, _type=None, from_first_fwd=True):
    attachments = []

    if _type is None:
        _type = ['audio', 'video', 'photo', 'doc']
    if _type is str:
        _type = [_type]
    if vk_event.attachments:
        for att in vk_event.attachments:
            if att['type'] in _type:
                attachments.append(att)
    if vk_event.fwd:
        if from_first_fwd:
            msgs = [vk_event.fwd[0]]
        else:
            msgs = vk_event.fwd
        for msg in msgs:
            if msg['attachments']:
                # ToDo: в зависимости от типа парсить те или иные атачменты
                fwd_attachments = vk_event.parse_attachments(msg['attachments'])
                for att in fwd_attachments:
                    if att['type'] in _type:
                        attachments.append(att)

    return attachments


# Ищет команду по имени
def find_command_by_name(command_name):
    from apps.bot.initial import get_commands
    commands = get_commands()

    for command in commands:
        if command.names and command_name in command.names:
            return command
    return None


# Получает detail_help_text для команды
def get_help_for_command(command):
    result = ""
    if len(command.names) > 1:
        result += f"Названия команды: {', '.join(command.names)}\n"
    if command.access != Role.USER:
        result += f"Необходимый уровень прав - {command.access.value}\n"
    if result:
        result += '\n'
    if command.detail_help_text:
        result += command.detail_help_text
    else:
        result += "У данной команды нет подробного описания"
    return result


# Коэффициент Танимото. Степерь схожести двух строк
def tanimoto(s1, s2):
    a, b, c = len(s1), len(s2), 0.0
    for sym in s1:
        if sym in s2:
            c += 1
    return c / (a + b - c)


def get_image_size_by_text(txt, font):
    testImg = Image.new('RGB', (1, 1))
    testDraw = ImageDraw.Draw(testImg)
    return testDraw.textsize(txt, font)


def draw_text_on_image(text):
    """
    :return: bytearray Image
    """
    fontsize = 16

    colorText = "black"
    colorBackground = "white"

    font = ImageFont.truetype(os.path.join(STATIC_ROOT, 'fonts/consolas.ttf'), fontsize, encoding="unic")
    width, height = get_image_size_by_text(text, font)
    width += 10
    height += 10
    img = Image.new('RGB', (width + 20, height + 20), colorBackground)
    d = ImageDraw.Draw(img)
    d.text((10, 10), text, fill=colorText, font=font)

    imgByteArr = io.BytesIO()
    img.save(imgByteArr, format='PNG')
    return imgByteArr

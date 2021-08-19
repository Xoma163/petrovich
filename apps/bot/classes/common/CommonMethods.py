import os
# Вероятность события в процентах
import random
import re
from datetime import datetime

import pytz
from PIL import Image, ImageDraw, ImageFont

from apps.bot.classes.Consts import Role
from apps.bot.classes.Exceptions import PWarning
from apps.service.models import Service
from petrovich.settings import STATIC_ROOT


def random_probability(probability) -> bool:
    """
    Возвращает True с заданной вероятностью
    """
    if 1 > probability > 99:
        raise PWarning("Вероятность события должна быть от 1 до 99")
    rand_int = get_random_int(1, 100)
    if rand_int <= probability:
        return True
    else:
        return False


def random_event(events, weights=None, seed=None):
    """
    Возвращает случайное событие с заданными вероятностями
    """
    if seed:
        random.seed(seed)
    if weights is None:
        random_choice = random.choice(events)
        random.seed()
        return random_choice
    random_choice = random.choices(events, weights=weights)[0]
    random.seed()
    return random_choice


def get_random_int(val1, val2=None, seed=None) -> int:
    """
    Возвращает рандомное число в заданном диапазоне. Если передан seed, то по seed
    """
    if not val2:
        val2 = val1
        val1 = 0
    if seed:
        random.seed(seed)
    random_int = random.randint(val1, val2)
    random.seed()
    return random_int


def has_cyrillic(text) -> bool:
    """
    Проверяет есть ли кириллица в тексте
    """
    return bool(re.search('[а-яА-Я]', text))


def remove_tz(dt):
    """
    Убирает временную зону у datetime
    """
    return dt.replace(tzinfo=None)


def localize_datetime(dt, tz):
    """
    Локализация datetime
    """
    tz_obj = pytz.timezone(tz)
    return pytz.utc.localize(dt, is_dst=None).astimezone(tz_obj)


def normalize_datetime(dt, tz):
    """
    Нормализация datetime
    """
    tz_obj = pytz.timezone(tz)
    localized_time = tz_obj.localize(dt, is_dst=None)

    tz_utc = pytz.timezone("UTC")
    return pytz.utc.normalize(localized_time, is_dst=None).astimezone(tz_utc)  # .replace(tzinfo=None)


def decl_of_num(number, titles):
    """
    Склоняет существительное после числительного
    number: число
    titles: 3 склонения
    """
    cases = [2, 0, 1, 1, 1, 2]
    if 4 < number % 100 < 20:
        return titles[2]
    elif number % 10 < 5:
        return titles[cases[number % 10]]
    else:
        return titles[cases[5]]


def get_attachments_for_upload(vk_bot, attachments):
    """
    Получает вложения и загружает необходимые на сервер, на которых нет прав
    Прикрепляет только фото, видео, аудио и документы.
    """
    uploaded_attachments = []
    for attachment in attachments:
        # Фото
        if attachment['type'] == 'photo':
            new_attachment = vk_bot.upload_photos(attachment['private_download_url'])
            uploaded_attachments.append(new_attachment[0])
        # Видео, аудио, документы
        elif 'vk_url' in attachment:
            uploaded_attachments.append(attachment['vk_url'])
    return uploaded_attachments


def get_attachments_from_attachments_or_fwd(vk_event, _type=None, from_first_fwd=True):
    """
    Получает все вложения из сообщения и пересланного сообщения
    """
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
                fwd_attachments = vk_event.parse_attachments(msg['attachments'])
                for att in fwd_attachments:
                    if att['type'] in _type:
                        attachments.append(att)

    return attachments


def find_command_by_name(command_name):
    """
    Ищет команду по имени
    """
    from apps.bot.initial import COMMANDS
    for command in COMMANDS:
        if command_name == command.name or (command.names and command_name in command.names):
            return command
    raise PWarning("Я не знаю такой команды")


def get_help_texts_for_command(command) -> str:
    """
    Получает help_texts для команды
    """
    result = ""
    if len(command.full_names) > 1:
        result += f"Названия команды: {', '.join(command.full_names)}\n"
    if command.access != Role.USER:
        result += f"Необходимый уровень прав - {command.access.value}\n"
    if result:
        result += '\n'
    if command.help_texts:
        result += command.full_help_texts
    else:
        result += "У данной команды нет подробного описания"
    return result


def tanimoto(s1, s2) -> float:
    """
    Коэффициент Танимото. Степерь схожести двух строк
    """
    a, b, c = len(s1), len(s2), 0.0
    for sym in s1:
        if sym in s2:
            c += 1
    return c / (a + b - c)


def get_image_size_by_text(txt, font):
    """
    Вычисление размеро текста если оно будет изображением
    """
    img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(img)
    return draw.textsize(txt, font)


def draw_text_on_image(text):
    """
    Рисование текста на изображении
    :return: bytearray Image
    """
    fontsize = 16

    text_color = "black"
    background_color = "white"

    font = ImageFont.truetype(os.path.join(STATIC_ROOT, 'fonts/consolas.ttf'), fontsize, encoding="unic")
    width, height = get_image_size_by_text(text, font)
    width += 10
    height += 10
    img = Image.new('RGB', (width + 20, height + 20), background_color)
    d = ImageDraw.Draw(img)
    d.text((10, 10), text, fill=text_color, font=font)

    # img_byte_arr = io.BytesIO()
    # img.save(img_byte_arr, format='PNG')
    return img


def get_role_by_str(role_str):
    """
    Получение роли по названию
    """
    who = None
    if role_str in ['администрация', 'администратор', 'админы', 'админ', 'главный', 'власть', 'господин']:
        who = Role.ADMIN
    elif role_str in ['moderators', 'moderator' 'модераторы', 'модератор', 'модеры', 'модер']:
        who = Role.MODERATOR
    elif role_str in ['майнкрафт уведомления', 'майн уведомления']:
        who = Role.MINECRAFT_NOTIFY
    elif role_str in ['майнкрафт', 'майн']:
        who = Role.MINECRAFT
    elif role_str in ['террария']:
        who = Role.TERRARIA
    elif role_str in ['забанен', 'бан']:
        who = Role.BANNED
    elif role_str in ['доверенный', 'проверенный']:
        who = Role.TRUSTED
    elif role_str in ['дом', 'домашний', 'дома']:
        who = Role.HOME

    return who


def check_command_time(name, seconds):
    """
    Проверка на то, прошло ли время с последнего выполнения команды и можно ли выполнять команду
    :param name: название команды
    :param seconds: количество времени, после которого разрешается повторно выполнить команду
    :return: bool
    """
    entity, created = Service.objects.get_or_create(name=name)
    if created:
        return True
    update_datetime = entity.update_datetime
    delta_time = datetime.utcnow() - remove_tz(update_datetime)
    if delta_time.seconds < seconds and delta_time.days == 0:
        error = f"Нельзя часто вызывать данную команду. Осталось {seconds - delta_time.seconds} секунд"
        raise PWarning(error)
    entity.name = name
    entity.save()
    return True


def transform_k(arg: str):
    """
    Перевод из строки с К в число. Пример: 1.3к = 1300
    :param arg: текстовое число с К
    :return: int
    """
    arg = arg.lower()
    count_m = arg.count('m') + arg.count('м')
    count_k = arg.count('k') + arg.count('к') + count_m * 2
    if count_k > 0:
        arg = arg \
            .replace('k', '') \
            .replace('к', '') \
            .replace('м', '') \
            .replace('m', '')
        arg = float(arg)
        arg *= 10 ** (3 * count_k)
    return arg


def replace_similar_letters(text):
    similar_letters = {
        'c': 'с',
        'e': 'е',
        'y': 'у',
        'o': 'о',
        'p': 'р',
        'k': 'к',
        'x': 'х',
        'n': 'п',
    }
    for letter in similar_letters:
        text = text.replace(letter, similar_letters[letter])
    return text

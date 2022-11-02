import io
import os
import random
import re
from datetime import datetime
from io import BytesIO
from typing import List

import pytz
from PIL import Image, ImageDraw, ImageFont

from apps.bot.classes.consts.Consts import Role, Platform, trans_table, trans_table_reverse
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.classes.messages.attachments.Attachment import Attachment
from apps.service.models import Service
from petrovich.settings import STATIC_ROOT


def random_probability(probability) -> bool:
    """
    Возвращает True с заданной вероятностью
    """
    if 0 > probability > 100:
        raise PWarning("Вероятность события должна быть от 0 до 100")
    rand_float = get_random_float(0, 100)
    if rand_float <= probability:
        return True
    else:
        return False


def random_event(events: list, weights: list = None, seed=None):
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


def get_random_int(val1: int, val2: int = None, seed=None) -> int:
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


def get_random_float(val1: float, val2: float = None, seed=None):
    if not val2:
        val2 = val1
        val1 = 0
    if seed:
        random.seed(seed)
    random_float = random.uniform(val1, val2)
    random.seed()
    return random_float


def has_cyrillic(text: str) -> bool:
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
    return pytz.utc.normalize(localized_time, is_dst=None).astimezone(tz_utc)


def decl_of_num(number, titles: List[str]):
    """
    Склоняет существительное после числительного
    number: число
    titles: 3 склонения
    """
    cases = [2, 0, 1, 1, 1, 2]
    if 4 < number % 100 < 20:
        return titles[2]
    elif number % 10 < 5:
        return titles[cases[int(number) % 10]]
    else:
        return titles[cases[5]]


def find_command_by_name(command_name: str):
    """
    Ищет команду по имени
    """
    from apps.bot.initial import COMMANDS
    for command in COMMANDS:
        if command_name == command.name or (command.names and command_name in command.names):
            return command
    raise PWarning("Я не знаю такой команды")


def get_help_texts_for_command(command, platform=None) -> str:
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
        if platform == Platform.TG:
            lines = command.full_help_texts.split("\n")
            full_help_texts_list = []
            for line in lines:
                dash_pos = line.find(" - ")
                if dash_pos == -1:
                    new_line = line
                else:
                    new_line = get_tg_formatted_text_line(line[:dash_pos]) + line[dash_pos:]
                full_help_texts_list.append(new_line)
            full_help_texts = "\n".join(full_help_texts_list)
            result += full_help_texts
        else:
            result += command.full_help_texts
    else:
        result += "У данной команды нет подробного описания"
    return result


def tanimoto(s1: str, s2: str) -> float:
    """
    Коэффициент Танимото. Степерь схожести двух строк
    """
    a, b, c = len(s1), len(s2), 0.0
    for sym in s1:
        if sym in s2:
            c += 1
    return c / (a + b - c)


def get_image_size_by_text(txt: str, font):
    """
    Вычисление размеро текста если оно будет изображением
    """
    img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(img)
    return draw.textsize(txt, font)


def draw_text_on_image(text: str):
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
    return img


def get_role_by_str(role_str: str):
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
    elif role_str in ['мразь', 'мразота', 'мрази']:
        who = Role.MRAZ
    elif role_str in ['пользователь', 'юзер']:
        who = Role.USER
    elif role_str in ['игрок', 'геймер', 'игроки', 'геймеры']:
        who = Role.GAMER

    return who


def check_command_time(name: str, seconds: int):
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


def replace_similar_letters(text: str):
    """
    Замена английский похожих букв на русские
    """
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


def get_thumbnail_for_image(image: Attachment, size) -> bytes:
    """
    Получение thumbnail для изображения
    """
    content = image.download_content()
    _image = Image.open(BytesIO(content))
    _image.thumbnail((size, size))
    thumb_byte_arr = io.BytesIO()
    _image.save(thumb_byte_arr, format="PNG")
    thumb_byte_arr.seek(0)
    return thumb_byte_arr.read()


def get_urls_from_text(text: str) -> list:
    """
    Поиск ссылок в тексте.
    Возвращает список найденных ссылок
    """
    return re.findall("(?P<url>https?://[^\s]+)", text)


def get_chunks(lst: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_flat_list(_list: List[List]):
    """
    Получение списка размерностью 1 из списка размерностью 2
    """
    return [item for sublist in _list for item in sublist]


def get_tg_formatted_text(text: str) -> str:
    """
    Форматированный текст в телеграмме (html)
    """
    return f"<pre>{text}</pre>"


def get_tg_formatted_text_line(text: str) -> str:
    """
    Форматированный текст в телеграмме в одну линию (html)
    """
    return f"<code>{text}</code>"


def get_tg_formatted_url(name, url) -> str:
    return f'<a href="{url}">{name}</a>'


def get_tg_underline_text(text: str) -> str:
    """
    Текст с нижним подчёркиванием в телеграмме (html)
    """
    return f"<u>{text}</u>"


def get_tg_italic_text(text: str) -> str:
    """
    Наклонный текст в телеграмме (html)
    """
    return f"<i>{text}</i>"


def get_tg_bold_text(text: str) -> str:
    """
    Жирный текст в телеграмме (html)
    """
    return f"<i>{text}</i>"


def get_tg_strike_text(text: str) -> str:
    """
    Жирный текст в телеграмме (html)
    """
    return f"<s>{text}</s>"


def fix_layout(s):
    new_s = ""
    for letter in s:
        if letter in trans_table:
            new_s += trans_table[letter]
        elif letter in trans_table_reverse:
            new_s += trans_table_reverse[letter]
        else:
            new_s += letter
    return new_s

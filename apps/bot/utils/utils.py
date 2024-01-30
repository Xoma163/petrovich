import io
import os
import random
import re
import time
from datetime import datetime
from io import BytesIO
from typing import List, Optional
from urllib.parse import urlparse

import pytz
from PIL import Image, ImageDraw, ImageFont

from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.attachments.attachment import Attachment
from apps.bot.classes.messages.response_message import ResponseMessageItem
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


def get_random_float(val1: float, val2: float = None, seed=None) -> float:
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


def remove_tz(dt: datetime) -> datetime:
    """
    Убирает временную зону у datetime
    """
    return dt.replace(tzinfo=None)


def localize_datetime(dt: datetime, tz: str) -> datetime:
    """
    Локализация datetime
    """
    tz_obj = pytz.timezone(tz)
    return pytz.utc.localize(dt, is_dst=None).astimezone(tz_obj)


def normalize_datetime(dt: datetime, tz: str) -> datetime:
    """
    Нормализация datetime
    """
    tz_obj = pytz.timezone(tz)
    localized_time = tz_obj.localize(dt, is_dst=None)

    tz_utc = pytz.timezone("UTC")
    return pytz.utc.normalize(localized_time).astimezone(tz_utc)


def decl_of_num(number, titles: List[str]) -> str:
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


def get_help_texts_for_command(command, platform=None, roles: List[Role] = None) -> str:
    """
    Получает help_texts для команды
    """

    DASH = "—"

    from apps.bot.classes.bots.tg_bot import TgBot
    from apps.bot.classes.help_text import HelpTextItemCommand

    if roles is None:
        roles = [Role.USER]

    result = ""
    if len(command.full_names) > 1:
        result += f"Названия команды: {', '.join(command.full_names)}\n"
    if command.access != Role.USER:
        result += f"Необходимый уровень прав {DASH} {command.access.value}\n"
    if result:
        result += '\n'
    if command.help_text:
        items: list[HelpTextItemCommand] = []
        for role in roles:
            if res := command.help_text.get_help_text_item(role):
                items += res.texts
        full_help_texts_list = []

        for item in items:
            if item.args:
                line = TgBot.get_formatted_text_line(f"/{command.name} {item.args}") + f" {DASH} {item.description}"
            else:
                line = TgBot.get_formatted_text_line(f"/{command.name}") + f" {DASH} {item.description}"
            full_help_texts_list.append(line)

        if command.help_text.extra_text:
            full_help_texts_list.append("")
            full_help_texts_list.append(command.help_text.extra_text)
            full_help_texts = "\n".join(full_help_texts_list)
            result += full_help_texts
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


def get_image_size_by_text(txt: str, font) -> (int, int):
    """
    Вычисление размеро текста если оно будет изображением
    """
    img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(img)
    box = draw.textbbox((0, 0), txt, font)
    w = box[2] - box[0]  # bottom-top
    h = box[3] - box[1]  # right-left
    return w, h


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

    roles_map = {
        ('администрация', 'администратор', 'админы', 'админ', 'главный', 'власть', 'господин', 'хозяин'): Role.ADMIN,
        ('moderators', 'moderator', 'модераторы', 'модератор', 'модеры', 'модер'): Role.MODERATOR,
        ('майнкрафт', 'майн'): Role.MINECRAFT,
        ('палворлд', 'пал'): Role.PALWORLD,
        ('забанен', 'бан'): Role.BANNED,
        ('доверенный', 'проверенный'): Role.TRUSTED,
        ('мразь', 'мразота', 'мрази'): Role.MRAZ,
        ('флейва',): Role.FLAIVA,
        ('пользователь', 'юзер'): Role.USER
    }
    for k in roles_map:
        if role_str in k:
            return roles_map[k]


def check_command_time(name: str, seconds: int):
    """
    Проверка на то, прошло ли время с последнего выполнения команды и можно ли выполнять команду
    :param name: название команды
    :param seconds: количество времени, после которого разрешается повторно выполнить команду
    :return: bool
    """
    entity, created = Service.objects.get_or_create(name=name)
    if created:
        return
    update_datetime = entity.update_datetime
    delta_time = datetime.utcnow() - remove_tz(update_datetime)
    if delta_time.seconds < seconds and delta_time.days == 0:
        error = f"Нельзя часто вызывать данную команду. Осталось {seconds - delta_time.seconds} секунд"
        raise PWarning(error)
    entity.name = name
    entity.save()


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


def get_flat_list(_list: List[List]) -> list:
    """
    Получение списка размерностью 1 из списка размерностью 2
    """
    return [item for sublist in _list for item in sublist]


eng_chars = u"~`!@#$%^&qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"
rus_chars = u"ёё!\"№;%:?йцукенгшщзхъфывапролджэячсмитьбю.ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,"
trans_table = dict(zip(eng_chars, rus_chars))
trans_table_reverse = dict(zip(rus_chars, eng_chars))


def fix_layout(s) -> str:
    new_s = ""
    for letter in s:
        if letter in trans_table:
            new_s += trans_table[letter]
        elif letter in trans_table_reverse:
            new_s += trans_table_reverse[letter]
        else:
            new_s += letter
    return new_s


def get_url_file_ext(url) -> str:
    return urlparse(url).path.rsplit('.', 1)[-1]


def send_message_session_or_edit(bot, event, session, rmi: ResponseMessageItem, max_delta):
    delta_messages = 0
    if event.message.id:
        delta_messages = event.message.id - session.message_id

    if delta_messages > max_delta:
        old_msg_id = session.message_id
        br = bot.send_response_message_item(rmi)
        message_id = br.response['result']['message_id']
        session.message_id = message_id
        session.save()
        bot.delete_messages(event.peer_id, old_msg_id)
    else:
        rmi.message_id = session.message_id
        br = bot.send_response_message_item(rmi)
    if not br.success and br.response.get('description') != \
            'Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message':
        rmi.message_id = None
        br = bot.send_response_message_item(rmi)
        message_id = br.response['result']['message_id']
        session.message_id = message_id
        session.save()
    bot.delete_messages(event.peer_id, event.message.id)


def prepend_symbols(string: str, symbol: str, n: int) -> str:
    """
    Добивает строку до N символов вставляя их перед строкой
    """
    n_symbols = n - len(string)
    if n_symbols > 0:
        return n_symbols * symbol + string
    return string


def append_symbols(string: str, symbol: str, n: int) -> str:
    """
    Добивает строку до N символов вставляя их после строки
    """
    n_symbols = n - len(string)
    if n_symbols > 0:
        return string + n_symbols * symbol
    return string


def replace_markdown_links(text: str, bot) -> str:
    p = re.compile(r"\[(.*)\]\(([^\)]*)\)")  # markdown links
    for item in reversed(list(p.finditer(text))):
        start_pos = item.start()
        end_pos = item.end()
        link_text = text[item.regs[1][0]:item.regs[1][1]]
        link = text[item.regs[2][0]:item.regs[2][1]]
        tg_url = bot.get_formatted_url(link_text, link)
        text = text[:start_pos] + tg_url + text[end_pos:]
    return text


def markdown_to_html(text: str, bot) -> str:
    text = text \
        .replace(">", "&gt;") \
        .replace("<", "&lt;") \
        .replace("&lt;pre&gt;", "<pre>") \
        .replace("&lt;/pre&gt;", "</pre>")

    if bot.PRE_TAG:
        if bot.CODE_TAG:
            text = replace_pre_tag(text, bot, '```', '```')
        else:
            text = replace_tag(text, '```', '```', f"<{bot.PRE_TAG}>", f"</{bot.PRE_TAG}>")

    if bot.CODE_TAG:
        text = replace_tag(text, '`', '`', f"<{bot.CODE_TAG}>", f"</{bot.CODE_TAG}>")
    if bot.BOLD_TAG:
        text = replace_tag(text, '**', '**', f"<{bot.BOLD_TAG}>", f"</{bot.BOLD_TAG}>")
    if bot.ITALIC_TAG:
        text = replace_tag(text, '*', '*', f"<{bot.ITALIC_TAG}>", f"</{bot.ITALIC_TAG}>")
    if bot.QUOTE_TAG:
        text = replace_tag(text, '\n&gt;', '\n', f"\n<{bot.QUOTE_TAG}>", f"</{bot.QUOTE_TAG}>\n")
    elif bot.CODE_TAG:
        text = replace_tag(text, '\n&gt;', '\n', f"\n<{bot.CODE_TAG}>", f"</{bot.CODE_TAG}>\n")
    if bot.LINK_TAG:
        text = replace_markdown_links(text, bot)
    return text


def replace_tag(text: str, start_tag: str, end_tag: str, new_start_tag: str, new_end_tag: str):
    start_tag_len = len(start_tag)
    end_tag_len = len(end_tag)

    start_tag_pos = 0
    while True:
        start_tag_pos = text.find(start_tag, start_tag_pos)
        end_tag_pos = text.find(end_tag, start_tag_pos + 1)

        if start_tag_pos == -1 or end_tag_pos == -1:
            break

        inner_to_replace = text[start_tag_pos:end_tag_pos + end_tag_len]
        # strip - экспериментально
        inner_text = text[start_tag_pos + start_tag_len:end_tag_pos].strip()
        new_inner = new_start_tag + inner_text + new_end_tag
        text = text.replace(inner_to_replace, new_inner)

        start_tag_pos = start_tag_pos + len(new_inner)
    return text


def replace_pre_tag(text: str, bot, start_tag: str, end_tag: str):
    start_tag_len = len(start_tag)
    end_tag_len = len(end_tag)

    start_tag_pos = 0
    while True:
        start_tag_pos = text.find(start_tag, start_tag_pos)
        end_tag_pos = text.find(end_tag, start_tag_pos + 1)

        if start_tag_pos == -1 or end_tag_pos == -1:
            break

        start_language_pos = start_tag_pos + start_tag_len
        end_language_pos = text.find('\n', start_tag_pos)
        language = text[start_language_pos:end_language_pos]
        if '`' in language or ' ' in language:
            language = ""

        inner_to_replace = text[start_tag_pos:end_tag_pos + end_tag_len]
        # strip - экспериментально
        inner_text = text[start_tag_pos + start_tag_len + 1 + len(language):end_tag_pos].strip()
        new_inner = bot.get_formatted_text(inner_text, language)
        text = text.replace(inner_to_replace, new_inner)

        start_tag_pos = start_tag_pos + len(new_inner)
    return text


def split_text_by_n_symbols(text: str, n: int, split_on: Optional[List[str]] = None) -> List[str]:
    """
    Разбивает текст на чанки с делением по спецсимволам указанным в split_on
    """
    if split_on is None:
        split_on = ['\n', ',', ' ', '']
    if len(text) < n:
        return [text]

    texts = []
    while len(text) > n:
        for split_on_symbol in split_on:
            split_by_pos = text.rfind(split_on_symbol, 0, n)
            if split_by_pos == -1:
                continue
            texts.append(text[:split_by_pos + 1])
            text = text[split_by_pos + 1:]
            break
    texts.append(text)
    return texts


def retry(times, exceptions, sleep_time=0):
    """
    Retry Decorator
    Retries the wrapped function/method `times` times if the exceptions listed
    in ``exceptions`` are thrown
    :param times: The number of times to repeat the wrapped function/method
    :type times: Int
    :param Exceptions: Lists of exceptions that trigger a retry attempt
    :type Exceptions: Tuple of Exceptions
    """

    def decorator(func):
        def newfn(*args, **kwargs):
            attempt = 0
            while attempt < times:
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    attempt += 1
                    if sleep_time:
                        time.sleep(sleep_time)
            return func(*args, **kwargs)

        return newfn

    return decorator

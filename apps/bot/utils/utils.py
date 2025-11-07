import io
import os
import random
import re
import zoneinfo
from datetime import datetime
from io import BytesIO
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont
from django.contrib.auth.models import Group

from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextKey
from apps.bot.classes.messages.attachments.document import DocumentAttachment
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.models import Profile
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
    Переводит из datetime UTC в datetime UTC, но с учетом офсета таймзоны
    """
    # Установим временную зону UTC и потом конвертируем в зону tz
    dt = dt.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
    return dt.astimezone(zoneinfo.ZoneInfo(tz))


def normalize_datetime(dt: datetime, tz: str) -> datetime:
    """
    Нормализация datetime
    """
    tz_obj = zoneinfo.ZoneInfo(tz)
    localized_time = dt.replace(tzinfo=tz_obj)
    return localized_time.astimezone(zoneinfo.ZoneInfo("UTC"))


def decl_of_num(number, titles: list[str]) -> str:
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


def get_help_texts_for_command(command, roles: list[Role] = None) -> str:
    """
    Получает help_texts для команды
    """
    DASH = "-"
    LONG_DASH = "—"
    DOUBLE_DASH = "--"

    from apps.bot.classes.bots.tg_bot import TgBot
    from apps.bot.classes.help_text import HelpTextArgument

    if roles is None:
        roles = [Role.USER]

    result = ""
    if len(command.full_names) > 1:
        result += f"Названия команды: {', '.join(command.full_names)}\n"
    if command.access != Role.USER:
        result += f"Необходимый уровень прав {LONG_DASH} {command.access}\n"
    if result:
        result += '\n'
    if command.help_text:
        _format = TgBot.get_formatted_text_line
        # help texts
        items: list[HelpTextArgument] = []
        for role in roles:
            if res := command.help_text.get_help_text_item(role):
                items += res.items
        full_help_texts_list = []

        for item in items:
            if item.args:
                full_command_name = _format(f"/{command.name} {item.args}")
            else:
                full_command_name = _format(f"/{command.name}")
            line = f"{full_command_name} {LONG_DASH} {item.description}"
            full_help_texts_list.append(line)

        # Отступ
        if full_help_texts_list:
            full_help_texts_list.append("")

        # help keys

        keys: list[HelpTextKey] = []
        for role in roles:
            if res := command.help_text.get_help_text_key(role):
                keys += res.items
        if keys:
            full_help_texts_list.append("Возможные ключи:")
        for key in keys:
            aliases = [key.key]
            aliases += key.get_aliases()
            full_keys = []
            for key_item in aliases:
                if len(key_item) == 1:
                    full_keys.append(_format(DASH + key_item))
                else:
                    full_keys.append(_format(DOUBLE_DASH + key_item))
            full_key = ", ".join(full_keys)
            line = f"{full_key} {LONG_DASH} {key.description}"
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


def get_image_size_by_text(txt: str, font) -> tuple[int, int]:
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

    font = get_font_by_path("consolas.ttf", fontsize)

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
        ('администрация', 'администратор', 'админы', 'админ', 'главный', 'власть', 'господин', 'хозяин', 'admin',
         'administrator'): Role.ADMIN,
        ('moderators', 'moderator', 'модераторы', 'модератор', 'модеры', 'модер', 'moder'): Role.MODERATOR,
        ('майнкрафт', 'майн', 'minecraft', 'mine'): Role.MINECRAFT,
        ('забанен', 'бан', 'ban', 'banned'): Role.BANNED,
        ('доверенный', 'проверенный', 'trust', 'trusted'): Role.TRUSTED,
        ('мразь', 'мразота', 'мрази', 'mraz'): Role.MRAZ,
        ('флейва', 'flaiva'): Role.FLAIVA,
        ('пользователь', 'юзер', 'user'): Role.USER
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


def get_urls_from_text(text: str) -> list:
    """
    Поиск ссылок в тексте.
    Возвращает список найденных ссылок
    """
    return re.findall(r"(?P<url>https?://[^\s]+)", text)


def get_chunks(lst: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_flat_list(_list: list[list]) -> list:
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
    p = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    for item in reversed(list(p.finditer(text))):
        start_pos, end_pos = item.span()
        link_text = item.group(1)
        link = item.group(2)
        tg_url = bot.get_formatted_url(link_text, link)
        text = text[:start_pos] + tg_url + text[end_pos:]
    return text


def markdown_wrap_symbols(text):
    return text \
        .replace(">", "&gt;") \
        .replace("<", "&lt;") \
        .replace("&lt;pre&gt;", "<pre>") \
        .replace("&lt;/pre&gt;", "</pre>")


def markdown_to_html(text: str, bot) -> str:
    text = markdown_wrap_symbols(text)
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

        # Не трогаем то, что внутри <code>
        # костыльненько
        to_replace_and_next = text[start_tag_pos:]
        close_code_block_pos = to_replace_and_next.find("</code>")
        open_code_block_pos = to_replace_and_next.find("<code")

        escape_tag = False
        if close_code_block_pos != -1:
            if open_code_block_pos != -1:
                if close_code_block_pos < open_code_block_pos:
                    escape_tag = True
            else:
                escape_tag = True

        if escape_tag:
            start_tag_pos += len(start_tag)
            continue

        # strip - экспериментально
        inner_text = text[start_tag_pos + start_tag_len:end_tag_pos].strip()
        new_inner = new_start_tag + inner_text + new_end_tag
        inner_to_replace = text[start_tag_pos:end_tag_pos + end_tag_len]
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
        # strip - плохо режет слева, rstrip - экспериментально
        inner_text = text[start_tag_pos + start_tag_len + 1 + len(language):end_tag_pos].rstrip()
        new_inner = bot.get_formatted_text(inner_text, language)
        text = text.replace(inner_to_replace, new_inner)

        start_tag_pos = start_tag_pos + len(new_inner)
    return text


def split_text_by_n_symbols(text: str, n: int, split_on: list[str] | None = None) -> list[str]:
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





def get_default_headers() -> dict:
    return {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }


def get_font_by_path(font_path: str, size: int) -> ImageFont:
    return ImageFont.truetype(os.path.join(STATIC_ROOT, f'fonts/{font_path}'), size, encoding="unic")


def make_thumbnail(
        photo_attachment: PhotoAttachment,
        max_size: int | None = None,
        use_proxy: bool = False
) -> io.BytesIO:
    """
    Центрирование изображение с блюром в пустотах
    Используется для получения thumbnail
    Принудительно переводится в jpeg
    """

    image_bytes = io.BytesIO(photo_attachment.download_content(use_proxy=use_proxy))
    image = Image.open(image_bytes).convert("RGB")
    # Проверяем, нужно ли уменьшить изображение
    if max_size and (image.width > max_size or image.height > max_size):
        # Вычисляем коэффициент уменьшения
        ratio = min(max_size / image.width, max_size / image.height)
        # Уменьшаем изображение пропорционально
        image = image.resize((int(image.width * ratio), int(image.height * ratio)), Image.Resampling.LANCZOS)

    # Преобразуем результат в JPEG
    jpeg_image_io = BytesIO()
    image.save(jpeg_image_io, format='JPEG')
    jpeg_image_io.seek(0)

    return jpeg_image_io


def prepare_filename(filename: str, replace_symbol=".") -> str:
    """
    Заменяет "плохие" символы в строке для корректного сохранения файла
    Обрезает по длине
    """
    escaped_replace_symbol = re.escape(replace_symbol)

    # Заменяем "плохие" символы на replace_symbol
    bad_symbols = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", "+"]
    for symbol in bad_symbols:
        # На случай, если символ считался разделителем, добавляем пробел справа
        filename = filename.replace(symbol, f"{replace_symbol} ")
    # Убираем пробелы с краёв
    filename = filename.strip()
    # Убираем последовательности replace_symbol до одного
    filename = re.sub(rf"{escaped_replace_symbol}+", replace_symbol, filename)
    # Убираем лишние пробелы до одного
    filename = re.sub(r"\s+", " ", filename)
    # Удаляем пробел перед точкой
    filename = filename.replace(f" {replace_symbol}", replace_symbol)
    # Максимальная длина - 255. Режем с конца, так как может потеряться расширение файла
    filename = filename[-255:]
    return filename


def get_admin_profile(exclude_profile: Profile | None = None) -> Profile | None:
    admin_group = Group.objects.get(name=Role.ADMIN.name)
    profile = Profile.objects.filter(groups__in=[admin_group]).first()

    if exclude_profile and profile == exclude_profile:
        return
    return profile


def wrap_text_in_document(text: str, filename: str = 'file.html') -> DocumentAttachment:
    text = text.replace("\n", "<br>")
    document = DocumentAttachment()
    document.parse(text.encode('utf-8-sig'), filename=filename)
    return document


def convert_jpg_to_png(image_bytes_jpg: bytes, image_mode="RGBA") -> bytes:
    image = Image.open(io.BytesIO(image_bytes_jpg))
    if image.mode != image_mode:
        image = image.convert(image_mode)
    output_buffer = io.BytesIO()
    # Сохраняем без дополнительных изменений
    image.save(output_buffer, format="PNG", quality=100)
    image_bytes_png = output_buffer.getvalue()
    return image_bytes_png


def crop_image_to_square(image_bytes: bytes) -> bytes:
    """
    Обрезает изображение по меньшей стороне,
    """
    # Читаем картинку из байтов
    img = Image.open(io.BytesIO(image_bytes))
    width, height = img.size
    # Размер стороны квадрата
    side = min(width, height)

    # Вычисляем отступы, чтобы центрировать квадратик
    left = (width - side) // 2
    top = (height - side) // 2
    right = left + side
    bottom = top + side

    square = img.crop((left, top, right, bottom))

    output_buffer = io.BytesIO()
    fmt = img.format or 'PNG'
    square.save(output_buffer, format=fmt)
    return output_buffer.getvalue()


def get_transparent_rgba_png(width, height):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def extract_json(text) -> str:
    start = text.find('{')
    if start == -1:
        raise ValueError('JSON не найден')

    depth = 0
    for i, char in enumerate(text[start:]):
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                end = start + i + 1
                break
    else:
        raise ValueError('Некорректный JSON: не сходятся скобки')
    json_str = text[start:end]
    return json_str

import datetime
import io
import os
import random
import re
import zoneinfo
from urllib.parse import urlparse, parse_qsl

from PIL import Image, ImageDraw, ImageFont

from apps.bot.consts import RoleEnum
from apps.bot.core.messages.attachments.document import DocumentAttachment
from apps.bot.models import Profile
from apps.bot.models import Role
from apps.commands.help_text import HelpTextKey
from apps.shared.exceptions import PWarning
from apps.shared.models import Service
from petrovich.settings import STATIC_ROOT


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


def remove_tz(dt: datetime.datetime) -> datetime.datetime:
    """
    Убирает временную зону у datetime
    """
    return dt.replace(tzinfo=None)


def localize_datetime(dt: datetime.datetime, tz: str) -> datetime.datetime:
    """
    Локализация datetime
    Переводит из datetime UTC в datetime UTC, но с учетом офсета таймзоны
    """
    # Установим временную зону UTC и потом конвертируем в зону tz
    dt = dt.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
    return dt.astimezone(zoneinfo.ZoneInfo(tz))


def normalize_datetime(dt: datetime.datetime, tz: str) -> datetime.datetime:
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


def get_help_texts_for_command(command, roles: list[RoleEnum] = None) -> str:
    """
    Получает help_texts для команды
    """
    DASH = "-"
    LONG_DASH = "—"
    DOUBLE_DASH = "--"

    from apps.bot.core.bot.telegram.tg_bot import TgBot
    from apps.commands.help_text import HelpTextArgument

    if roles is None:
        roles = [RoleEnum.USER]

    result = ""
    if len(command.full_names) > 1:
        result += f"Названия команды: {', '.join(command.full_names)}\n"
    if command.access != RoleEnum.USER:
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
         'administrator'): RoleEnum.ADMIN,
        ('moderators', 'moderator', 'модераторы', 'модератор', 'модеры', 'модер', 'moder'): RoleEnum.MODERATOR,
        ('майнкрафт', 'майн', 'minecraft', 'mine'): RoleEnum.MINECRAFT,
        ('забанен', 'бан', 'ban', 'banned'): RoleEnum.BANNED,
        ('доверенный', 'проверенный', 'trust', 'trusted'): RoleEnum.TRUSTED,
        ('пользователь', 'юзер', 'user'): RoleEnum.USER
    }
    for k in roles_map:
        if role_str in k:
            return roles_map[k]
    return None


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
    delta_time = datetime.datetime.now(datetime.UTC) - update_datetime
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


def get_font_by_path(font_path: str, size: int) -> type[ImageFont]:
    return ImageFont.truetype(os.path.join(STATIC_ROOT, f'fonts/{font_path}'), size, encoding="unic")


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
    admin_role = Role.objects.get(name=RoleEnum.ADMIN.name)
    profile = Profile.objects.filter(roles__in=[admin_role]).first()

    if exclude_profile and profile == exclude_profile:
        return None
    return profile


def wrap_text_in_document(text: str, filename: str = 'file.html') -> DocumentAttachment:
    text = text.replace("\n", "<br>")
    document = DocumentAttachment()
    document.parse(text.encode('utf-8-sig'), filename=filename)
    return document


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


def get_youtube_video_id(url) -> str | None:
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname.replace('www.', '').lower()

    if hostname == 'youtube.com':
        query_dict = {x[0]: x[1] for x in parse_qsl(parsed_url.query)}
        if video_id := query_dict.get('v', None):
            return video_id
        return parsed_url.path.replace("/shorts", "").strip("/")
    elif hostname == 'youtu.be':
        return parsed_url.path.strip('/')
    return None


def detect_ext(b: bytes) -> str | None:
    if not b:
        return None

    if b.startswith(b'\xFF\xD8\xFF'):
        return "jpg"

    if b.startswith(b'GIF87a') or b.startswith(b'GIF89a'):
        return "gif"

    if len(b) >= 12 and b[4:8] == b'ftyp':
        return "mp4"
    idx = b.find(b'ftyp', 0, 64)
    if idx != -1 and idx + 4 + 4 <= len(b):
        return "mp4"

    if b.startswith(b'OggS'):
        return "ogg"

    if len(b) >= 12 and b[0:4] == b'RIFF' and b[8:12] == b'WEBP':
        return "webp"

    if b.startswith(b'\x1A\x45\xDF\xA3') and b'webm' in b[:4096].lower():
        return "webm"

    return None


def convert_pil_image_to_bytes(pil_image, _format="PNG") -> bytes:
    img_byte_arr = io.BytesIO()
    pil_image.save(img_byte_arr, format=_format)
    img_byte_arr.seek(0)
    return img_byte_arr.read()

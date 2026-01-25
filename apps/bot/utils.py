from threading import Lock

from django.db.models import Q

from apps.bot.consts import PlatformEnum
from apps.bot.core.messages.response_message import ResponseMessageItem
from apps.bot.models import Chat, Profile, User, Bot
from apps.shared.exceptions import PWarning
from petrovich.settings import env

lock = Lock()


def get_user_by_id(user_id, platform: PlatformEnum, _defaults: dict = None) -> User:
    """
    Получение пользователя по его id
    """
    if not _defaults:
        _defaults = {}
    defaults = {}
    defaults.update(_defaults)

    with lock:
        user, _ = User.objects.get_or_create(
            user_id=user_id,
            platform=platform.name,
            defaults=defaults
        )
    return user


def get_profile_by_user_id(user_id, platform: PlatformEnum):
    user = get_user_by_id(user_id, platform)
    profile = get_profile_by_user(user)
    return profile


def get_profile_by_user(user: User, _defaults: dict = None) -> Profile:
    """
    Возвращает профиль по пользователю
    """
    if not _defaults:
        _defaults = {}
    defaults = {}
    defaults.update(_defaults)

    if not user.profile:
        with lock:
            profile = Profile(**defaults)
            profile.save()
            user.profile = profile
            user.save()

    return user.profile


def get_profile_by_name(filters: list, filter_chat=None) -> Profile:
    """
    Получение пользователя по имени/фамилии/имени и фамилии/никнейма/ид
    """
    users = Profile.objects.all()
    if filter_chat:
        users = users.filter(chats=filter_chat)

    for _filter in filters:
        q = Q(name__icontains=_filter) | Q(surname__icontains=_filter) | Q(nickname_real__icontains=_filter)
        users = users.filter(q)

    if len(users) == 0:
        filters_str = " ".join(filters)
        raise PWarning(f"Пользователь {filters_str} не найден. Возможно опечатка или он мне ещё ни разу не писал")
    elif len(users) > 1:
        raise PWarning("2 и более пользователей подходит под поиск")

    return users.first()


def get_chat_by_id(chat_id: int, platform: PlatformEnum) -> Chat:
    """
    Возвращает чат по его id
    """
    with lock:
        chat, _ = Chat.objects.get_or_create(
            chat_id=chat_id, platform=platform.name
        )
    return chat


def get_bot_by_id(bot_id: int, platform: PlatformEnum) -> Bot:
    """
    Возвращает бота по его id
    """
    if bot_id > 0:
        bot_id = -bot_id
    with lock:
        bot, _ = Bot.objects.get_or_create(
            bot_id=bot_id, platform=platform.name
        )
    return bot


def add_profile_to_chat(profile: Profile, chat: Chat):
    """
    Добавление чата пользователю
    """
    with lock:
        chats = profile.chats
        if chat not in chats.all():
            chats.add(chat)


def remove_profile_from_chat(profile: Profile, chat: Chat):
    """
    Удаление чата пользователю
    """
    with lock:
        chats = profile.chats
        if chat in chats.all():
            chats.remove(chat)


def send_message_to_moderator_chat(msg: ResponseMessageItem):
    moderator_chat_pk = env.str("TG_MODERATOR_CHAT_PK")
    moderator_chat_id = Chat.objects.get(pk=moderator_chat_pk).chat_id

    from apps.bot.core.bot.telegram.tg_bot import TgBot
    bot = TgBot()
    msg.peer_id = moderator_chat_id
    return bot.send_response_message_item(msg)

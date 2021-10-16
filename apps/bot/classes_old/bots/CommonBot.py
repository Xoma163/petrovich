import logging
import traceback
from copy import deepcopy
from threading import Thread
from urllib.parse import urlparse

from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.classes.consts.Exceptions import PSkip, PWarning, PError
from apps.bot.classes.events.Event import Event
from apps.bot.models import Users, Chat, Bot
from apps.bot.utils.utils import tanimoto
from apps.games.models import Gamer
from apps.service.models import Meme


class CommonBot(Thread):
    def __init__(self, platform):
        Thread.__init__(self)

        self.platform = platform
        self.mentions = []
        self.user_model = Users.objects.filter(platform=self.platform.name)
        self.chat_model = Chat.objects.filter(platform=self.platform.name)
        self.bot_model = Bot.objects.filter(platform=self.platform.name)

        self.logger = logging.getLogger(platform.value)

    def get_user_by_id(self, user_id) -> Users:
        """
        Возвращает пользователя по его id
        """
        raise NotImplementedError

    def get_chat_by_id(self, chat_id) -> Chat:
        """
        Возвращает чат по его id
        """
        raise NotImplementedError

    def get_bot_by_id(self, bot_id) -> Bot:
        """
        Получение бота по его id
        """
        raise NotImplementedError

    @staticmethod
    def need_reaction_for_fwd(event):
        message = event['message']['text']

        fwd_message = None
        if event.get('fwd'):
            fwd_message = event['fwd'][0]['text']

        from apps.bot.commands.TrustedCommands.Media import MEDIA_URLS
        message_is_media_link = urlparse(message).hostname in MEDIA_URLS or \
                                (fwd_message and urlparse(fwd_message) in MEDIA_URLS)
        if message_is_media_link:
            return True

    @staticmethod
    def parse_date(date) -> str:
        """
        Парсинг даты
        """
        date_arr = date.split('.')
        if len(date_arr) == 2:
            return f"1970-{date_arr[1]}-{date_arr[0]}"
        else:
            return f"{date_arr[2]}-{date_arr[1]}-{date_arr[0]}"

    @staticmethod
    def add_chat_to_user(user, chat):
        """
        Добавление чата пользователю
        """
        chats = user.chats
        if chat not in chats.all():
            chats.add(chat)

    @staticmethod
    def remove_chat_from_user(user, chat):
        """
        Удаление чата пользователю
        """
        chats = user.chats
        if chat in chats.all():
            chats.remove(chat)



    def delete_message(self, chat_id, message_id):
        """
        Удаление сообщения
        """
        raise NotImplementedError

    def get_one_chat_with_user(self, chat_name, user_id):
        """
        Получение чата по названию, в котором есть пользователь
        """
        chats = self.chat_model.filter(name__icontains=chat_name)
        if len(chats) == 0:
            raise PWarning("Не нашёл такого чата")

        chats_with_user = []
        for chat in chats:
            user_contains = chat.users.filter(user_id=user_id)
            if user_contains:
                chats_with_user.append(chat)

        if len(chats_with_user) == 0:
            raise PWarning("Не нашёл доступного чата с пользователем в этом чате")
        elif len(chats_with_user) > 1:
            chats_str = '\n'.join(chats_with_user)
            raise PWarning("Нашёл несколько чатов. Уточните какой:\n"
                           f"{chats_str}")

        elif len(chats_with_user) == 1:
            return chats_with_user[0]

    @staticmethod
    def get_gamer_by_user(user) -> Gamer:
        """
        Получение игрока по модели пользователя
        """

        gamers = Gamer.objects.filter(user=user)
        if len(gamers) == 0:
            gamer = Gamer(user=user)
            gamer.save()
            return gamer
        elif len(gamers) > 1:
            raise PWarning("Два и более игрока подходит под поиск")
        else:
            return gamers.first()


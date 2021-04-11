import traceback

from django.contrib.auth.models import Group

from apps.bot.classes.Consts import Platform, Role
from apps.bot.classes.bots.CommonBot import CommonBot
from apps.bot.classes.events.YandexEvent import YandexEvent
from apps.bot.models import Users, Chat, Bot


class YandexBot(CommonBot):
    def __init__(self):
        CommonBot.__init__(self, Platform.YANDEX)

    def set_activity(self, peer_id, activity='typing'):
        """
        Метод позволяет указать пользователю, что бот набирает сообщение или записывает голосовое
        Используется при длительном выполнении команд, чтобы был фидбек пользователю, что его запрос принят
        """
        pass

    def get_user_by_id(self, user_id) -> Users:
        """
        Возвращает пользователя по его id
        """
        yandex_user = self.user_model.filter(user_id=user_id)
        if len(yandex_user) > 0:
            yandex_user = yandex_user.first()
        else:
            # Если пользователь из fwd
            yandex_user = Users()
            yandex_user.user_id = user_id
            yandex_user.platform = self.platform.name

            yandex_user.save()

            group_user = Group.objects.get(name=Role.USER.name)
            yandex_user.groups.add(group_user)
            yandex_user.save()
        return yandex_user

    def get_chat_by_id(self, chat_id) -> Chat:
        """
        Возвращает чат по его id
        """
        pass

    def get_bot_by_id(self, bot_id) -> Bot:
        """
        Получение бота по его id
        """
        pass

    @staticmethod
    def add_extra_group_to_user(user, chat):
        """
        Добавляет дополнительные группы пользователям из уникальных чатов
        """
        pass

    def send_message(self, peer_id: str, msg: str = "ᅠ", attachments=None, keyboard=None,
                     dont_parse_links: bool = False, **kwargs):
        """
        Отправка сообщения
        peer_id: в какой чат/какому пользователю
        msg: сообщение
        attachments: список вложений
        keyboard: клавиатура
        dont_parse_links: не преобразовывать ссылки
        """
        pass

    def _setup_event_before(self, event):
        """
        Подготовка события перед проверкой на то, нужен ли ответ
        """
        yandex_event = {
            'platform': self.platform,
            'from_user': True,
            'chat_id': None,
            'user_id': event['session']['user']['user_id'],
            'peer_id': None,
            'message': {
                'text': event['request']['command'],
                'payload': None,
                'attachments': [],  # event.message.attachments,
                'action': None
            },
            'fwd': None
        }

        # Как только мы заходим в навык, message['text'] = ''. Здороваемся с пользователем
        if not yandex_event['message']['text']:
            yandex_event['message']['text'] = "привет"
        return yandex_event

    def need_a_response(self, yandex_event):
        """
        Нужен ли ответ пользователю
        """
        return self.need_a_response_common(yandex_event)

    def _setup_event_after(self, yandex_event):
        """
        Подготовка события после проверки на то, нужен ли ответ
        Нужно это для того, чтобы не тратить ресурсы на обработку если она не будет востребована
        """
        yandex_event['sender'] = self.get_user_by_id(yandex_event['user_id'])
        return yandex_event

    def listen(self):
        """
        Получение новых событий и их обработка
        """
        pass

    def parse(self, event):
        try:
            # Если пришло новое сообщение
            yandex_event = self._setup_event_before(event)
            if not self.need_a_response(yandex_event):
                return
            yandex_event = self._setup_event_after(yandex_event)
            yandex_event_object = YandexEvent(yandex_event)
            # threading.Thread(target=self.menu, args=(vk_event_object,)).start()
            command_result = self.menu(yandex_event_object, send=False)
            result = self.parse_command_result(command_result)
            return self.prepare_yandex_response(result)
        except Exception as e:
            print(str(e))
            tb = traceback.format_exc()
            print(tb)

    @staticmethod
    def prepare_yandex_response(msgs):
        msg = msgs[0]  # Только 1 сообщение
        return {
            "response": {
                "text": msg['msg'],
                "end_session": True
            },
            "version": "1.0"
        }

    @staticmethod
    def _prepare_obj_to_upload(file_like_object, allowed_exts_url=None):
        """
        """
        pass

    def upload_photos(self, images, max_count=10):
        """
        """
        pass

    def upload_animation(self, animation, peer_id=None, title='Документ'):
        """
        """
        pass

    def upload_document(self, document, peer_id=None, title='Документ'):
        """
        """
        pass

    def upload_audio(self, audio, artist, title):
        """
        """
        pass

    @staticmethod
    def get_inline_keyboard(command_text, button_text="Ещё", args=None):
        """
        """
        pass

    @staticmethod
    def get_group_id(_id) -> str:
        """
        Получение group_id по короткому id
        """
        pass

    @staticmethod
    def get_mention(user: Users, name=None):
        """
        Получение меншона пользователя
        """
        pass

    def upload_video_by_link(self, link, name):
        """
        Загрузка видео по ссылке со стороннего ресурса
        """
        pass

    def get_attachment_by_id(self, _type, group_id, _id):
        """
        Получение ссылки для вложения
        """
        pass

    def get_video(self, owner_id, _id):
        """
        Получение данных о видео
        """
        pass

    def set_chat_title(self, chat_id, title):
        """
        Изменение названия конфы
        """
        pass

    def set_chat_title_if_not_equals(self, chat_id, title):
        """
        Изменение названия конфы если оно не равно предыдущему, иначе будет дубликат изменения
        """
        pass

    def get_conference_users(self, peer_id):
        """
        Получения списка пользователей конфы
        """
        pass

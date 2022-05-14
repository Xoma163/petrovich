import json
import threading

import vk_api
from vk_api import VkApi, VkUpload
from vk_api.utils import get_random_id

from apps.bot.classes.bots.Bot import Bot as CommonBot
from apps.bot.classes.bots.vk.MyVkBotLongPoll import MyVkBotLongPoll
from apps.bot.classes.consts.ActivitiesEnum import VK_ACTIVITIES, ActivitiesEnum
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.events.VkEvent import VkEvent
from apps.bot.classes.messages.ResponseMessage import ResponseMessageItem, ResponseMessage
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.commands.Profile import add_city_to_db
from apps.bot.models import Bot as BotModel, Profile, User
from petrovich.settings import env, VK_URL


class VkBot(CommonBot):

    def __init__(self):
        CommonBot.__init__(self, Platform.VK)

        self.token = env.str('VK_BOT_TOKEN')
        self.group_id = env.str('VK_BOT_GROUP_ID')
        vk_session = VkApi(token=self.token, api_version="5.131", config_filename="secrets/vk_bot_config.json")
        self.longpoll = MyVkBotLongPoll(vk_session, group_id=self.group_id)
        self.upload = VkUpload(vk_session)
        self.vk = vk_session.get_api()

    # MAIN ROUTING AND MESSAGING

    def listen(self):
        """
        Получение новых событий и их обработка
        """
        for raw_event in self.longpoll.listen():
            vk_event = VkEvent(raw_event, self)
            threading.Thread(target=self.handle_event, args=(vk_event,)).start()

    def send_response_message(self, rm: ResponseMessage):
        """
        Отправка ResponseMessage сообщения
        Вовзращает список результатов отправки в формате
        [{success:bool, response:Response, response_message_item:ResponseMessageItem}]
        """
        results = []
        for rmi in rm.messages:
            try:
                response = self.send_response_message_item(rmi)
                results.append({"success": True, "response": response, "response_message_item": rmi})
            except vk_api.exceptions.ApiError as e:
                if e.code not in [901, 917]:
                    error_rm = ResponseMessage(self.ERROR_MSG, rmi.peer_id).messages[0]
                    self.logger.error({'message': self.ERROR_MSG, 'error': str(e)})
                    response = self.send_response_message_item(error_rm)
                    results.append({"success": False, "response": response, "response_message_item": error_rm})
        return results

    def send_response_message_item(self, rm: ResponseMessageItem):
        """
        Отправка ResponseMessageItem сообщения
        Возвращает Response платформы
        """
        text = str(rm.text)
        if len(text) > 4096:
            text = text[:4092]
            text += "\n..."

        attachments = []
        for att in rm.attachments:
            if isinstance(att, str):
                attachments.append(att)
            elif att.url:
                attachments.append(att.url)
            elif att.public_download_url:
                attachments.append(att.public_download_url)

        return self.vk.messages.send(
            peer_id=rm.peer_id,
            message=text,
            access_token=self.token,
            random_id=get_random_id(),
            attachment=','.join(attachments),
            keyboard=json.dumps(rm.keyboard),
        )

    # END MAIN ROUTING AND MESSAGING

    # ATTACHMENTS

    def upload_photos(self, images, max_count=10, peer_id=None):
        """
        Загрузка фотографий на сервер ТГ.
        images: список изображений в любом формате (ссылки, байты, файлы)
        При невозможности загрузки одной из картинки просто пропускает её
        """
        atts = super().upload_photos(images, max_count)
        parsed_atts = []
        for pa in atts:
            try:
                url, public_download_url = self.upload_photo_and_urls(pa)
                pa.url = url.replace(VK_URL, '')
                pa.public_download_url = public_download_url
                parsed_atts.append(pa)
            except Exception:
                continue
        return parsed_atts

    def upload_photo_and_urls(self, image: PhotoAttachment):
        """
        Загрузка изображения на сервер VK
        Возвращает vk_url и public_download_url
        """
        vk_photo = self.upload.photo_messages(image.get_bytes_io_content())[0]
        vk_url = f"{VK_URL}photo{vk_photo['owner_id']}_{vk_photo['id']}"
        vk_max_photo_url = sorted(vk_photo['sizes'], key=lambda x: x['height'])[-1]['url']
        return vk_url, vk_max_photo_url

    def upload_document(self, document, peer_id=None, title='Документ', filename=None):
        """
        Загрузка документа на сервер ВК.
        """
        da = super().upload_document(document, peer_id, title, filename)
        content = da.download_content()
        vk_doc = self.upload.document_message(content, title=title, peer_id=peer_id)['doc']
        return f"doc{vk_doc['owner_id']}_{vk_doc['id']}"

    # END ATTACHMENTS

    # USERS GROUPS BOTS

    def get_profile_by_user(self, user: User, is_new=False, _defaults: dict = None) -> Profile:
        """
        Возвращает пользователя по его id
        Регистрирует если пользователя нет в БД
        """
        if not user.profile:
            vk_user = self.get_user_info(int(user.user_id))
            profile = Profile()
            profile.name = vk_user['first_name']
            profile.surname = vk_user['last_name']
            profile.platform = self.platform.name
            profile.set_avatar(vk_user['photo_max'])

            if 'sex' in vk_user:
                profile.gender = vk_user['sex']
            if 'city' in vk_user:
                from apps.service.models import City
                city_name = vk_user['city']['title']
                city = City.objects.filter(name__icontains=city_name)
                if len(city) > 0:
                    city = city.first()
                else:
                    try:
                        city = add_city_to_db(city_name)
                    except Exception:
                        city = None
                profile.city = city
            else:
                profile.city = None
            if 'screen_name' in vk_user:
                user.nickname = vk_user['screen_name']
            with self.lock:
                profile.save()
                user.profile = profile
                user.save()
            return super().get_profile_by_user(user, is_new=True)
        return super().get_profile_by_user(user)

    def get_user_info(self, user_id: int):
        """
        Получение информации о пользователе
        """
        return self.vk.users.get(user_id=user_id, lang='ru', fields='sex, bdate, city, screen_name, photo_max')[0]

    def update_profile_avatar(self, profile: Profile, user_id):
        """
        Обновление аватара пользователя
        """
        user_info = self.get_user_info(user_id)
        profile.set_avatar(user_info['photo_max'])

    def get_bot_by_id(self, bot_id: int) -> BotModel:
        """
        Получение информации о боте
        """
        try:
            bot = self.bot_model.get(bot_id=bot_id)
        except BotModel.DoesNotExist:
            bot = super().get_bot_by_id(bot_id)
            vk_bot = self.get_bot_info(bot_id)
            bot.name = vk_bot['name']
            bot.set_avatar(vk_bot['photo_200'])
            bot.save()
        return bot

    def get_bot_info(self, bot_id):
        """
        Получение информации о боте
        """
        return self.vk.groups.getById(group_id=bot_id)[0]

    def update_bot_avatar(self, bot_id):
        """
        Обновление аватара бота
        """
        bot = self.get_bot_by_id(bot_id)
        bot_info = self.get_bot_info(bot_id)
        bot.name = bot_info['name']
        bot.set_avatar(bot_info['photo_200'])

    # END USERS GROUPS BOTS

    # EXTRA

    def set_activity(self, peer_id, activity: ActivitiesEnum):
        """
        Метод позволяет указать пользователю, что бот набирает сообщение или записывает голосовое
        Используется при длительном выполнении команд, чтобы был фидбек пользователю, что его запрос принят
        """
        tg_activity = VK_ACTIVITIES.get(activity)
        if tg_activity:
            self.vk.messages.setActivity(type=tg_activity, peer_id=peer_id, group_id=self.group_id)

    @staticmethod
    def get_button(text, command, args=None):
        return {
            'action': {
                'type': 'text',
                'label': text,
                "payload": json.dumps({
                    "command": command,
                    "args": args,
                }, ensure_ascii=False)
            },
            'color': 'primary',
        }

    def get_inline_keyboard(self, buttons: list, cols=1):
        """
        param buttons: ToDo:
        Получение инлайн-клавиатуры с кнопками
        В основном используется для команд, где нужно запускать много команд и лень набирать заново
        """
        keyboard = super().get_inline_keyboard(buttons)
        return {
            'inline': True,
            'buttons': keyboard
        }

    def get_mention(self, profile: Profile, name=None):
        """
        Получение меншона пользователя
        """
        user = profile.get_user_by_platform(self.platform)
        name = name or str(user)
        return f"[id{user.user_id}|{name}]"

    def remove_self_from_chat(self, chat_id):
        """
        Удаление бота (себя) из чата
        """
        self.vk.messages.removeChatUser(chat_id=chat_id, member_id=f"-{self.group_id}")

    def get_conversation_messages(self, peer_id, conversation_message_id):
        """
        Получение полного сообщения
        """
        response = self.vk.messages.getByConversationMessageId(
            peer_id=peer_id,
            conversation_message_ids=[conversation_message_id]
        )
        return response['items'][0]
    # END EXTRA

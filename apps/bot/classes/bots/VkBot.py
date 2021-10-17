import json
import threading
from io import BytesIO

import vk_api
from vk_api import VkApi, VkUpload
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.utils import get_random_id

from apps.bot.classes.bots.Bot import Bot as CommonBot
from apps.bot.classes.consts.ActivitiesEnum import VK_ACTIVITIES, ActivitiesEnum
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.events.VkEvent import VkEvent
from apps.bot.classes.messages.ResponseMessage import ResponseMessageItem, ResponseMessage
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.models import Bot as BotModel
from apps.bot.utils.utils import get_chunks
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
        """
        for msg in rm.messages:
            try:
                self.send_message(msg)
            except vk_api.exceptions.ApiError as e:
                if e.code == 901:
                    pass
                error_msg = "Непредвиденная ошибка. Сообщите разработчику. Команда /баг"
                error_rm = ResponseMessage(error_msg, msg.peer_id).messages[0]
                self.logger.error({'result': error_msg, 'error': f"{e.code} {e.error}"})
                self.send_message(error_rm)

    def send_message(self, rm: ResponseMessageItem):
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

        self.vk.messages.send(
            peer_id=rm.peer_id,
            message=text,
            access_token=self.token,
            random_id=get_random_id(),
            attachment=','.join(attachments),
            keyboard=json.dumps(rm.keyboard),
            # dont_parse_links=dont_parse_links
        )

    def upload_photos(self, images, max_count=10):
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
        Сохраняет изображение на серверах VK
        Возвращает vk_url и public_download_url
        """
        image_to_load = image.download_content()
        vk_photo = self.upload.photo_messages(BytesIO(image_to_load))[0]
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
        return f"doc{vk_doc['owner_id']}{vk_doc['id']}"

    def set_activity(self, peer_id, activity: ActivitiesEnum):
        """
        Метод позволяет указать пользователю, что бот набирает сообщение или записывает голосовое
        Используется при длительном выполнении команд, чтобы был фидбек пользователю, что его запрос принят
        """
        tg_activity = VK_ACTIVITIES.get(activity)
        if tg_activity:
            self.vk.messages.setActivity(type=tg_activity, peer_id=peer_id, group_id=self.group_id)

    @staticmethod
    def get_inline_keyboard(buttons: list, cols=1):

        """
        param buttons: [(button_name, args), ...]
        Получение инлайн-клавиатуры с одной кнопкой
        В основном используется для команд, где нужно запускать много команд и лень набирать заново
        """

        def get_buttons(_buttons):
            return [{
                'action': {
                    'type': 'text',
                    'label': button_item['button_text'],
                    "payload": json.dumps({
                        "command": button_item['command'],
                        "args": button_item.get('args'),
                    }, ensure_ascii=False)
                },
                'color': 'primary',
            } for button_item in _buttons]

        for i, _ in enumerate(buttons):
            if 'args' not in buttons[i] or buttons[i]['args'] is None:
                buttons[i]['args'] = {}
        buttons_chunks = get_chunks(buttons, cols)
        return {
            'inline': True,
            'buttons': [get_buttons(chunk) for chunk in buttons_chunks]
        }

    def update_bot_avatar(self, bot_id):
        """
        Обновление аватара боту для цитат
        """
        bot = self.get_bot_by_id(bot_id)
        bot_info = self.get_bot_info(bot_id)
        bot.name = bot_info['name']
        bot.set_avatar(bot_info['photo_200'])

    def get_bot_by_id(self, bot_id: int) -> BotModel:
        """
        Получение бота по его id
        """
        try:
            bot = self.bot_model.get(bot_id=bot_id)
        except self.bot_model.DoesNotExist:
            bot = super().get_bot_by_id(bot_id)
            vk_bot = self.get_bot_info(bot_id)
            bot.name = vk_bot['name']
            bot.set_avatar(vk_bot['photo_200'])
            bot.save()
        return bot

    def get_bot_info(self, bot_id):
        return self.vk.groups.getById(group_id=bot_id)[0]


class MyVkBotLongPoll(VkBotLongPoll):
    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as e:
                error = {'exception': f'Longpoll Error (VK): {str(e)}'}
                print(error)

import json
import threading

from apps.bot.classes.bots.Bot import Bot as CommonBot
from apps.bot.classes.bots.tg.MyTgBotLongPoll import MyTgBotLongPoll
from apps.bot.classes.bots.tg.TgRequests import TgRequests
from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum, TG_ACTIVITIES
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PError, PWarning, PSkip
from apps.bot.classes.events.Event import Event
from apps.bot.classes.events.TgEvent import TgEvent
from apps.bot.classes.messages.ResponseMessage import ResponseMessageItem, ResponseMessage
from apps.bot.classes.messages.attachments.DocumentAttachment import DocumentAttachment
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.StickerAttachment import StickerAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.commands.Meme import Meme
from apps.bot.models import Profile
from apps.bot.utils.utils import get_thumbnail_for_image, get_tg_formatted_url
from petrovich.settings import env


class TgBot(CommonBot):

    def __init__(self):
        CommonBot.__init__(self, Platform.TG)
        self.token = env.str("TG_TOKEN")
        self.requests = TgRequests(self.token)
        self.longpoll = MyTgBotLongPoll(self.token)

    # MAIN ROUTING AND MESSAGING

    def run(self):
        """
        Thread запуск основного тела команды
        """
        self.longpoll.set_last_update_id()
        return super().run()

    def listen(self):
        """
        Получение новых событий и их обработка
        """
        for raw_event in self.longpoll.listen():
            tg_event = TgEvent(raw_event, self)
            threading.Thread(target=self.handle_event, args=(tg_event,)).start()

    # _set_last_update_id

    def route(self, event: Event) -> ResponseMessage:
        if isinstance(event, TgEvent) and event.inline_mode:
            self.route_inline_mode(event)
            raise PSkip()

        return super().route(event)

    def route_inline_mode(self, event):
        data = event.inline_data

        filter_list = event.inline_data['message'].clear.split(' ')
        filter_list = filter_list if filter_list[0] else []
        meme_cmd = Meme(self, event)
        inline_query_result = meme_cmd.get_tg_inline_memes(filter_list)
        params = {
            'inline_query_id': data['id'],
            'results': json.dumps(inline_query_result, ensure_ascii=False),
            # 'cache_time': 0
        }
        response = self.requests.get('answerInlineQuery', params)
        if response.status_code != 200:
            response_json = response.json()
            error_msg = "Ошибка в inline_memes"
            self.logger.error({'message': error_msg, 'error': response_json})

    def _send_media_group(self, rm: ResponseMessageItem, default_params):
        """
        Отправка множества вложений. Ссылки
        """
        media = []
        for attachment in rm.attachments:
            if attachment.file_id:
                media.append({'type': attachment.type, 'media': attachment.file_id, 'caption': rm.text})
            elif attachment.public_download_url:
                media.append({'type': attachment.type, 'media': attachment.public_download_url, 'caption': rm.text})

        del default_params['caption']
        default_params['media'] = json.dumps(media)
        return self.requests.get('sendMediaGroup', default_params)

    def _send_photo(self, rm: ResponseMessageItem, default_params):
        """
        Отправка фото. Ссылка или файл
        """
        self.set_activity(default_params['chat_id'], ActivitiesEnum.UPLOAD_PHOTO)
        photo: PhotoAttachment = rm.attachments[0]
        if photo.file_id:
            default_params['photo'] = photo.file_id
            return self.requests.get('sendPhoto', default_params)
        if photo.public_download_url:
            default_params['photo'] = photo.public_download_url
            return self.requests.get('sendPhoto', default_params)
        else:
            if photo.get_size_mb() > 5:
                rm.attachments = []
                raise PError("Нельзя загружать видео более 40 мб в телеграмм")
            return self.requests.get('sendPhoto', default_params, files={'photo': photo.content})

    def _send_document(self, rm: ResponseMessageItem, default_params):
        """
        Отправка документа. Ссылка или файл
        """
        self.set_activity(default_params['chat_id'], ActivitiesEnum.UPLOAD_DOCUMENT)
        document: DocumentAttachment = rm.attachments[0]
        if document.public_download_url:
            default_params['document'] = document.public_download_url
            return self.requests.get('sendDocument', default_params)
        else:
            files = {'document': document.content}
            try:
                files['thumb'] = get_thumbnail_for_image(document, size=320)
            except Exception:
                pass
            return self.requests.get('sendDocument', default_params, files=files)

    def _send_video(self, rm: ResponseMessageItem, default_params):
        """
        Отправка видео. Ссылка или файл
        """
        self.set_activity(default_params['chat_id'], ActivitiesEnum.UPLOAD_VIDEO)
        video: VideoAttachment = rm.attachments[0]
        if video.public_download_url:
            default_params['video'] = video.public_download_url
            return self.requests.get('sendVideo', default_params)
        else:
            if video.get_size_mb() > 40:
                rm.attachments = []
                raise PError("Нельзя загружать видео более 40 мб в телеграмм")
            return self.requests.get('sendVideo', default_params, files={'video': video.content})

    def _send_sticker(self, rm: ResponseMessageItem, default_params):
        """
        Отправка стикера
        """
        sticker: StickerAttachment = rm.attachments[0]
        default_params['sticker'] = sticker.file_id
        return self.requests.get('sendSticker', default_params)

    def _send_text(self, default_params):
        self.set_activity(default_params['chat_id'], ActivitiesEnum.TYPING)
        default_params['text'] = default_params.pop('caption')
        return self.requests.get('sendMessage', default_params)

    def send_response_message(self, rm: ResponseMessage) -> list:
        """
        Отправка ResponseMessage сообщения
        Вовзращает список результатов отправки в формате
        [{success:bool, response:Response, response_message_item:ResponseMessageItem}]
        """
        results = []
        for rmi in rm.messages:
            try:
                rmi.set_telegram_html()
                response = self.send_response_message_item(rmi)

                # Непредвиденная ошибка
                if response.status_code != 200:
                    error_msg = "Непредвиденная ошибка. Сообщите разработчику. Команда /баг"
                    error_rm = ResponseMessage(error_msg, rmi.peer_id).messages[0]
                    self.logger.error({'message': error_msg, 'error': response.json()['description']})
                    response = self.send_response_message_item(error_rm)
                    results.append({"success": False, "response": response, "response_message_item": error_rm})
                else:
                    results.append({"success": True, "response": response, "response_message_item": rmi})
            # Предвиденная ошибка
            except (PWarning, PError) as e:
                rmi.text += f"\n\n{str(e)}"
                getattr(self.logger, e.level)({'message': rmi})
                response = self.send_response_message_item(rmi)
                results.append({"success": True, "response": response, "response_message_item": rmi})
        return results

    def send_response_message_item(self, rm: ResponseMessageItem):
        """
        Отправка ResponseMessageItem сообщения
        Возвращает Response платформы
        """
        params = {'chat_id': rm.peer_id, 'caption': rm.text, 'reply_markup': json.dumps(rm.keyboard)}
        params.update(rm.kwargs)
        if rm.attachments:
            if len(rm.attachments) > 1:
                return self._send_media_group(rm, params)
            elif isinstance(rm.attachments[0], PhotoAttachment):
                return self._send_photo(rm, params)
            elif isinstance(rm.attachments[0], VideoAttachment):
                return self._send_video(rm, params)
            elif isinstance(rm.attachments[0], DocumentAttachment):
                return self._send_document(rm, params)
            elif isinstance(rm.attachments[0], StickerAttachment):
                return self._send_sticker(rm, params)
        return self._send_text(params)

    # END  MAIN ROUTING AND MESSAGING

    # USERS GROUPS BOTS
    def update_profile_avatar(self, profile: Profile, user_id):
        response = self.requests.get('getUserProfilePhotos', {'user_id': user_id})
        photos = response.json()['result']['photos']
        if len(photos) == 0:
            raise PWarning("Нет фотографий в профиле")
        pa = PhotoAttachment()
        pa.parse_tg_photo(photos[0][-1], self)

        profile.set_avatar(pa.private_download_url)

    # END USERS GROUPS BOTS

    # EXTRA

    @staticmethod
    def _get_keyboard_buttons(_buttons):
        """
        Определение структуры кнопок
        """
        return [{
            'text': button_item['button_text'],
            'callback_data': json.dumps({
                'command': button_item['command'],
                "args": button_item.get('args'),
            }, ensure_ascii=False)
        } for button_item in _buttons]

    def get_inline_keyboard(self, buttons: list, cols=1):
        """
        param buttons: ToDo:
        Получение инлайн-клавиатуры с кнопками
        В основном используется для команд, где нужно запускать много команд и лень набирать заново
        """
        keyboard = super().get_inline_keyboard(buttons)
        return {
            'inline_keyboard': keyboard
        }

    def set_activity(self, peer_id, activity: ActivitiesEnum):
        """
        Метод позволяет указать пользователю, что бот набирает сообщение или записывает голосовое
        Используется при длительном выполнении команд, чтобы был фидбек пользователю, что его запрос принят
        """
        tg_activity = TG_ACTIVITIES[activity]

        # no wait for response
        threading.Thread(
            target=self.requests.get,
            args=(
                'sendChatAction',
                {'chat_id': peer_id, 'action': tg_activity}
            )
        ).start()

    def get_mention(self, profile: Profile, name=None):
        """
        Получение меншона пользователя
        """
        user = profile.get_user_by_platform(self.platform)
        return get_tg_formatted_url(str(profile), f"tg://user?id={user.user_id}")
        # if user.nickname:
        #     return f"@{user.nickname}"
        # return str(user)

    def delete_message(self, peer_id, message_id):
        """
        Удаление одного сообщения
        """
        self.requests.get('deleteMessage', params={'chat_id': peer_id, 'message_id': message_id})

    def upload_image_to_tg_server(self, url) -> PhotoAttachment:
        """
        Загрузка изображения на сервера ТГ с костылями

        Без бутылки не разобраться. У телеги нет встроенных методов по тупой загрузке файлов, поэтому приходится
        Отправлять сообщение в пустую конфу, забирать оттуда file_id и уже потом формировать сообщение
        """

        photo_uploading_chat = self.chat_model.get(pk=env.str("TG_PHOTO_UPLOADING_CHAT_PK"))
        pa = PhotoAttachment()
        pa.public_download_url = url
        rm = ResponseMessage({'attachments': [pa]}, peer_id=photo_uploading_chat.chat_id)
        response = self.send_response_message_item(rm.messages[0])
        if response.status_code != 200:
            raise PWarning
        r_json = response.json()
        self.delete_message(photo_uploading_chat.chat_id, r_json['result']['message_id'])
        uploaded_image = r_json['result']['photo'] if response.status_code == 200 else response
        pa.file_id = uploaded_image[-1]['file_id']
        return pa

    def update_help_texts(self):
        """
        Обновление списка команд в телеграме
        """

        from apps.bot.initial import COMMANDS
        commands_with_tg_name = list(filter(lambda x: x.name_tg, COMMANDS))
        help_texts_tg = [x.full_help_texts_tg.split(' - ') for x in commands_with_tg_name]
        help_texts_tg = [{'command': x[0], 'description': x[1]} for x in help_texts_tg]
        help_texts_tg.sort(key=lambda x: x['command'])
        self.requests.get('setMyCommands', json={'commands': help_texts_tg})

    def get_sticker_set(self, name):
        res = self.requests.get('getStickerSet', json={'name': name}).json()
        return res['result']['stickers']
    # END EXTRA
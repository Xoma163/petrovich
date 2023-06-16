import json
import threading

import requests
from numpy import inf

from apps.bot.classes.bots.Bot import Bot as CommonBot
from apps.bot.classes.bots.tg.MyTgBotLongPoll import MyTgBotLongPoll
from apps.bot.classes.bots.tg.TgRequests import TgRequests, TgRequestLocal
from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum, TG_ACTIVITIES
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PError, PWarning, PSkip
from apps.bot.classes.events.Event import Event
from apps.bot.classes.events.TgEvent import TgEvent
from apps.bot.classes.messages.ResponseMessage import ResponseMessageItem, ResponseMessage
from apps.bot.classes.messages.attachments.Attachment import Attachment
from apps.bot.classes.messages.attachments.AudioAttachment import AudioAttachment
from apps.bot.classes.messages.attachments.DocumentAttachment import DocumentAttachment
from apps.bot.classes.messages.attachments.GifAttachment import GifAttachment
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.StickerAttachment import StickerAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.classes.messages.attachments.VideoNoteAttachment import VideoNoteAttachment
from apps.bot.classes.messages.attachments.VoiceAttachment import VoiceAttachment
from apps.bot.commands.Meme import Meme
from apps.bot.models import Profile, Chat
from apps.bot.utils.utils import get_thumbnail_for_image, get_chunks
from petrovich.settings import env


class TgBot(CommonBot):
    TG_SERVER = 0
    LOCAL_SERVER = 1
    MODE = LOCAL_SERVER

    MAX_VIDEO_SIZE_MB = 50 if MODE == TG_SERVER else 2000
    MAX_ATTACHMENT_SIZE_MB = 20 if MODE == TG_SERVER else inf
    MAX_PHOTO_SIZE = 5 if MODE == TG_SERVER else inf
    MAX_GIF_SIZE = 40 if MODE == TG_SERVER else inf

    def __init__(self):
        CommonBot.__init__(self, Platform.TG)
        self.token = env.str("TG_TOKEN")
        if self.MODE == self.TG_SERVER:
            self.requests = TgRequests(self.token)
        else:
            self.requests = TgRequestLocal(self.token)

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
            self.parse(raw_event)

    def parse(self, raw_event):
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
            'cache_time': 0
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
        files = []
        for attachment in rm.attachments:
            if attachment.file_id:
                media.append({'type': attachment.type, 'media': attachment.file_id})
            elif attachment.public_download_url:
                media.append({'type': attachment.type, 'media': attachment.public_download_url})
            else:
                files.append({'type': attachment.type, 'media': attachment.content})

        if len(media) > 0:
            media[0]['caption'] = rm.text
        # if len(files) > 0:
        #     files[0]['caption'] = rm.text

        del default_params['caption']
        default_params['media'] = json.dumps(media)
        if not files:
            return self.requests.get('sendMediaGroup', default_params)
        else:
            return self.requests.get('sendMediaGroup', default_params, files=files)

    def _send_photo(self, rm: ResponseMessageItem, default_params):
        """
        Отправка фото. Ссылка или файл
        """
        self.set_activity_thread(default_params['chat_id'], ActivitiesEnum.UPLOAD_PHOTO)
        photo: PhotoAttachment = rm.attachments[0]
        if photo.file_id:
            default_params['photo'] = photo.file_id
            return self.requests.get('sendPhoto', default_params)
        if photo.public_download_url:
            default_params['photo'] = photo.public_download_url
            return self.requests.get('sendPhoto', default_params)
        else:
            if photo.get_size_mb() > self.MAX_PHOTO_SIZE:
                rm.attachments = []
                raise PError(f"Нельзя загружать фото более {self.MAX_PHOTO_SIZE} мб в телеграмм")
            return self.requests.get('sendPhoto', default_params, files={'photo': photo.content})

    def _send_document(self, rm: ResponseMessageItem, default_params):
        """
        Отправка документа. Ссылка или файл
        """
        self.set_activity_thread(default_params['chat_id'], ActivitiesEnum.UPLOAD_DOCUMENT)
        document: DocumentAttachment = rm.attachments[0]
        if document.file_id:
            default_params['document'] = document.file_id
            return self.requests.get('sendDocument', default_params)
        elif document.public_download_url:
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
        self.set_activity_thread(default_params['chat_id'], ActivitiesEnum.UPLOAD_VIDEO)
        video: VideoAttachment = rm.attachments[0]
        files = {'video': video.content}
        if video.thumb:
            files['thumb'] = requests.get(video.thumb).content
        if video.public_download_url:
            default_params['video'] = video.public_download_url
            return self.requests.get('sendVideo', default_params)
        elif video.file_id:
            default_params['video'] = video.file_id
            return self.requests.get('sendVideo', default_params)
        else:
            if video.get_size_mb() > self.MAX_VIDEO_SIZE_MB:
                rm.attachments = []
                raise PError(
                    f"Нельзя загружать видео более {self.MAX_VIDEO_SIZE_MB} мб в телеграмм. Ваше видео {round(video.get_size_mb(), 2)} мб")
            return self.requests.get('sendVideo', default_params, files=files)

    def _send_video_note(self, rm: ResponseMessageItem, default_params):
        """
        Отправка видео. Ссылка или файл
        """
        self.set_activity_thread(default_params['chat_id'], ActivitiesEnum.UPLOAD_VIDEO_NOTE)
        video_note: VideoNoteAttachment = rm.attachments[0]
        default_params['video_note'] = video_note.file_id
        return self.requests.get('sendVideoNote', default_params)

    def _send_audio(self, rm: ResponseMessageItem, default_params):
        """
        Отправка аудио. Ссылка или файл
        """
        self.set_activity_thread(default_params['chat_id'], ActivitiesEnum.UPLOAD_AUDIO)
        audio: AudioAttachment = rm.attachments[0]

        if audio.artist:
            default_params['performer'] = audio.artist
        if audio.title:
            default_params['title'] = audio.title

        if audio.public_download_url:
            default_params['audio'] = audio.public_download_url
            return self.requests.get('sendAudio', default_params)
        else:
            files = {'audio': audio.content}
            if audio.thumb:
                thumb_file = self.get_photo_attachment(audio.thumb, guarantee_url=True)
                files['thumb'] = thumb_file.get_bytes_io_content(default_params['chat_id'])
            return self.requests.get('sendAudio', default_params, files=files)

    def _send_gif(self, rm: ResponseMessageItem, default_params):
        """
        Отправка гифы. Ссылка или файл
        """
        self.set_activity_thread(default_params['chat_id'], ActivitiesEnum.UPLOAD_VIDEO)
        gif: GifAttachment = rm.attachments[0]
        if gif.public_download_url:
            default_params['animation'] = gif.public_download_url
            return self.requests.get('sendAnimation', default_params)
        elif gif.file_id:
            default_params['animation'] = gif.file_id
            return self.requests.get('sendAnimation', default_params)
        else:
            if gif.get_size_mb() > self.MAX_GIF_SIZE:
                rm.attachments = []
                raise PError(f"Нельзя загружать гифы более {self.MAX_GIF_SIZE} мб в телеграмм")
            return self.requests.get('sendAnimation', default_params, files={'animation': gif.content})

    def _send_sticker(self, rm: ResponseMessageItem, default_params):
        """
        Отправка стикера
        """
        sticker: StickerAttachment = rm.attachments[0]
        default_params['sticker'] = sticker.file_id
        return self.requests.get('sendSticker', default_params)

    def _send_voice(self, rm: ResponseMessageItem, default_params):
        """
        Отправка голосовухи
        """
        self.set_activity_thread(default_params['chat_id'], ActivitiesEnum.UPLOAD_AUDIO)
        voice: VoiceAttachment = rm.attachments[0]
        default_params['voice'] = voice.file_id
        return self.requests.get('sendVoice', default_params)

    def _send_text(self, default_params):
        self.set_activity(default_params['chat_id'], ActivitiesEnum.TYPING)
        default_params['text'] = default_params.pop('caption')
        if len(default_params['text']) > 4096:
            # Шлём длинные сообщения чанками. Последний чанк через return
            chunks = list(get_chunks(default_params['text'], 4096))
            for chunk in chunks[:-1]:
                default_params['text'] = chunk
                self.requests.get('sendMessage', default_params)
            default_params['text'] = chunks[-1]
        r = self.requests.get('sendMessage', default_params)
        return r

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

                # Непредвиденная ошибка телеги
                if response.status_code == 200:
                    results.append({"success": True, "response": response, "response_message_item": rmi})
                else:
                    skip_errors = [
                        "Bad Request: canceled by new editMessageMedia request",
                        "Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message"
                    ]
                    catch_errors = {
                        'Bad Request: VOICE_MESSAGES_FORBIDDEN': "Не могу отправить голосовуху из-за ваших настроек безопасности"
                    }
                    self.logger.error({'message': self.ERROR_MSG, 'error': response.json()['description']})
                    error = response.json()['description']
                    if error in skip_errors:
                        results.append({"success": False, "response": response, "response_message_item": rmi})
                    elif error in catch_errors:
                        msg = catch_errors[error]
                        warn_rm = ResponseMessage(msg, rmi.peer_id, rmi.message_thread_id).messages[0]
                        response = self.send_response_message_item(warn_rm)
                        results.append({"success": False, "response": response, "response_message_item": response})
                    else:
                        error_rm = ResponseMessage(self.ERROR_MSG, rmi.peer_id, rmi.message_thread_id).messages[0]
                        response = self.send_response_message_item(error_rm)
                        results.append({"success": False, "response": response, "response_message_item": response})
            # Предвиденная ошибка
            except (PWarning, PError) as e:
                _error_rmi = ResponseMessageItem(e.msg, rmi.peer_id, rmi.message_thread_id)
                getattr(self.logger, e.level)({'message': _error_rmi})
                response = self.send_response_message_item(_error_rmi)
                results.append({"success": False, "response": response, "response_message_item": _error_rmi})
        return results

    def edit_message(self, rm: ResponseMessageItem, params):
        if rm.attachments:
            return self.edit_media(rm, params)
        if rm.keyboard and not rm.text:
            return self.edit_keyboard(params)
        params['text'] = params.pop('caption')
        r = self.requests.get('editMessageText', params=params)
        return r

    def edit_keyboard(self, params):
        del params['caption']
        r = self.requests.get('editMessageReplyMarkup', params=params)
        return r

    def edit_media(self, rm, params):
        att: Attachment = rm.attachments[0]
        params['media'] = {'type': att.type}
        if att.file_id:
            params['media']['media'] = att.file_id
        if att.public_download_url:
            params['media']['media'] = att.public_download_url
        params['media'] = json.dumps(params['media'])
        r = self.requests.get('editMessageMedia', params=params)
        return r

    def send_response_message_item(self, rm: ResponseMessageItem):
        """
        Отправка ResponseMessageItem сообщения
        Возвращает Response платформы
        """
        params = {'chat_id': rm.peer_id, 'caption': rm.text, 'reply_markup': json.dumps(rm.keyboard)}
        params.update(rm.kwargs)

        if rm.reply_to:
            params['reply_to_message_id'] = rm.reply_to
        if rm.message_thread_id:
            params['message_thread_id'] = rm.message_thread_id

        if rm.message_id:
            params['message_id'] = rm.message_id
            return self.edit_message(rm, params)

        att_map = {
            PhotoAttachment: self._send_photo,
            GifAttachment: self._send_gif,
            VideoAttachment: self._send_video,
            VideoNoteAttachment: self._send_video_note,
            AudioAttachment: self._send_audio,
            DocumentAttachment: self._send_document,
            StickerAttachment: self._send_sticker,
            VoiceAttachment: self._send_voice,
        }

        if rm.attachments:
            try:
                if len(rm.attachments) > 1:
                    return self._send_media_group(rm, params)
                else:
                    return att_map[rm.attachments[0].__class__](rm, params)
            finally:
                self.stop_activity_thread()
        return self._send_text(params)

    # END  MAIN ROUTING AND MESSAGING

    # USERS GROUPS BOTS
    def update_profile_avatar(self, profile: Profile, user_id):
        response = self.requests.get('getUserProfilePhotos', {'user_id': user_id})
        photos = response.json()['result']['photos']
        if len(photos) == 0:
            raise PWarning("Нет фотографий в профиле")
        pa = PhotoAttachment()
        pa.parse_tg(photos[0][-1])

        profile.set_avatar(pa)

    # END USERS GROUPS BOTS

    # EXTRA

    @staticmethod
    def get_button(text, command, args=None, kwargs=None, url=None):
        callback_data = {"c": command}
        if args:
            callback_data['a'] = args
        if kwargs:
            callback_data['k'] = kwargs
        callback_data = json.dumps(callback_data, ensure_ascii=False)

        callback_data_len = len(callback_data.encode("UTF8"))
        if callback_data_len > 62:
            raise RuntimeError("Нельзя в callback_data передавать данные более 64 байт")
        data = {
            'text': text,
            'callback_data': callback_data
        }
        if url:
            data['url'] = url
        return data

    def get_inline_keyboard(self, buttons: list, cols=1):
        """
        param buttons: ToDo:
        Получение инлайн-клавиатуры с кнопками
        В основном используется для команд, где нужно запускать много команд и лень набирать заново
        """
        keyboard = super().get_inline_keyboard(buttons, cols)
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
        user = profile.get_tg_user()
        return self.get_formatted_url(str(profile), f"tg://user?id={user.user_id}")
        # if user.nickname:
        #     return f"@{user.nickname}"

    def delete_message(self, peer_id, message_id):
        """
        Удаление одного сообщения
        """
        self.requests.get('deleteMessage', params={'chat_id': peer_id, 'message_id': message_id})

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

    def set_chat_admin_title(self, chat_id, user_id, title):
        res = self.requests.get('setChatAdministratorCustomTitle', json={
            'chat_id': chat_id,
            'user_id': user_id,
            'custom_title': title
        }).json()
        return res

    def promote_chat_member(self, chat_id, user_id):
        res = self.requests.get('promoteChatMember', json={
            'chat_id': chat_id,
            'user_id': user_id,
            'can_manage_chat': False,
            'can_pin_messages': True,
        }).json()
        return res

    def get_file_id(self, attachment):
        uploading_chat = Chat.objects.get(pk=env.str("TG_PHOTO_UPLOADING_CHAT_PK"))
        r = self.parse_and_send_msgs({'attachments': [attachment]}, uploading_chat.chat_id)
        r_json = r[0]['response'].json()
        self.delete_message(uploading_chat.chat_id, r_json['result']['message_id'])
        att = r_json['result'][attachment.type]
        if isinstance(att, list):
            att = att[0]
        file_id = att['file_id']
        return file_id

    @classmethod
    def get_formatted_text(cls, text: str) -> str:
        """
        Форматированный текст
        """
        return f"<pre>{text}</pre>"

    @classmethod
    def get_formatted_text_line(cls, text: str) -> str:
        """
        Форматированный текст в одну линию
        """
        return f"<code>{text}</code>"

    @classmethod
    def get_formatted_url(cls, name, url) -> str:
        return f'<a href="{url}">{name}</a>'

    @classmethod
    def get_underline_text(cls, text: str) -> str:
        """
        Текст с нижним подчёркиванием
        """
        return f"<u>{text}</u>"

    @classmethod
    def get_italic_text(cls, text: str) -> str:
        """
        Наклонный текст
        """
        return f"<i>{text}</i>"

    @classmethod
    def get_bold_text(cls, text: str) -> str:
        """
        Жирный текст
        """
        return f"<b>{text}</b>"

    @classmethod
    def get_strike_text(cls, text: str) -> str:
        """
        Жирный текст
        """
        return f"<s>{text}</s>"

    @classmethod
    def get_spoiler_text(cls, text: str) -> str:
        """
        Спойлер-текст
        """
        return f'<span class="tg-spoiler">{text}</span>'

    # END EXTRA

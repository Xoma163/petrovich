import json
import threading
from copy import copy

from numpy import inf

from apps.bot.classes.bot_response import BotResponse
from apps.bot.classes.bots.bot import Bot
from apps.bot.classes.bots.tg.request import Request, RequestLocal
from apps.bot.classes.const.activities import ActivitiesEnum, TG_ACTIVITIES
from apps.bot.classes.const.consts import Platform
from apps.bot.classes.const.exceptions import PError, PWarning, PSkip
from apps.bot.classes.event.event import Event
from apps.bot.classes.event.tg_event import TgEvent
from apps.bot.classes.messages.attachments.attachment import Attachment
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.document import DocumentAttachment
from apps.bot.classes.messages.attachments.gif import GifAttachment
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.attachments.sticker import StickerAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.classes.messages.attachments.videonote import VideoNoteAttachment
from apps.bot.classes.messages.attachments.voice import VoiceAttachment
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.commands.meme import Meme
from apps.bot.models import Profile, Chat
from apps.bot.utils.utils import get_thumbnail_for_image, split_text_by_n_symbols, get_chunks
from petrovich.settings import env


class TgBot(Bot):
    TG_SERVER = 0
    LOCAL_SERVER = 1

    MODE = LOCAL_SERVER

    MAX_VIDEO_SIZE_MB = 50 if MODE == TG_SERVER else 2000
    MAX_ATTACHMENT_SIZE_MB = 20 if MODE == TG_SERVER else inf
    MAX_PHOTO_SIZE = 5 if MODE == TG_SERVER else inf
    MAX_GIF_SIZE = 40 if MODE == TG_SERVER else inf

    MAX_MESSAGE_TEXT_LENGTH = 4096
    MAX_MESSAGE_TEXT_CAPTION = 1024

    def __init__(self):
        Bot.__init__(self, Platform.TG)
        self.token = env.str("TG_TOKEN")
        if self.MODE == self.TG_SERVER:
            self.requests = Request(self.token)
        else:
            self.requests = RequestLocal(self.token)

    # MAIN ROUTING AND MESSAGING

    def run(self):
        """
        Thread запуск основного тела команды
        """
        return super().run()

    def parse(self, raw_event):
        tg_event = TgEvent(raw_event)
        threading.Thread(target=self.handle_event, args=(tg_event,)).start()

    def route(self, event: Event) -> ResponseMessage:
        if isinstance(event, TgEvent) and event.inline_mode:
            self.route_inline_mode(event)
            raise PSkip()

        return super().route(event)

    def route_inline_mode(self, event) -> dict:
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
        r = self.requests.get('answerInlineQuery', params).json()
        return r

    def _send_media_group(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка множества вложений. Ссылки
        """
        params = copy(default_params)
        media_list = []
        files = []
        for i, attachment in enumerate(rmi.attachments):
            if attachment.file_id:
                media = {'type': attachment.type, 'media': attachment.file_id}
            elif attachment.public_download_url:
                media = {'type': attachment.type, 'media': attachment.public_download_url}
            else:
                filename = attachment.name if attachment.name else str(i)
                files.append((filename, attachment.content))
                media = {'type': attachment.type, "media": f"attach://{filename}"}

            if getattr(attachment, 'artist', None):
                media['performer'] = attachment.artist
            if getattr(attachment, 'title', None):
                media['title'] = attachment.title
            if getattr(attachment, 'thumb', None):
                thumb_file = self.get_photo_attachment(attachment.thumb, guarantee_url=True)
                thumb_filename = f"thumb_{str(i)}"
                files.append((thumb_filename, thumb_file.get_bytes_io_content()))
                media['thumbnail'] = f"attach://{thumb_filename}"

            media_list.append(media)

        media_list[0]['caption'] = default_params['caption']

        del params['caption']
        params['media'] = json.dumps(media_list)
        if not files:
            r = self.requests.get('sendMediaGroup', params).json()
        else:
            r = self.requests.get('sendMediaGroup', params, files=files).json()
        return r

    def _send_photo(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка фото. Ссылка или файл
        """
        params = copy(default_params)
        photo: PhotoAttachment = rmi.attachments[0]
        if photo.file_id:
            params['photo'] = photo.file_id
            r = self.requests.get('sendPhoto', params).json()
        elif photo.public_download_url:
            params['photo'] = photo.public_download_url
            r = self.requests.get('sendPhoto', params).json()
        else:
            if photo.get_size_mb() > self.MAX_PHOTO_SIZE:
                rmi.attachments = []
                raise PError(f"Нельзя загружать фото более {self.MAX_PHOTO_SIZE} мб в телеграмм")
            r = self.requests.get('sendPhoto', params, files={'photo': photo.content}).json()
        return r

    def _send_document(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка документа. Ссылка или файл
        """
        params = copy(default_params)
        document: DocumentAttachment = rmi.attachments[0]
        if document.file_id:
            params['document'] = document.file_id
            r = self.requests.get('sendDocument', params).json()
        elif document.public_download_url:
            params['document'] = document.public_download_url
            r = self.requests.get('sendDocument', params).json()
        else:
            files = {'document': document.content}
            try:
                files['thumbnail'] = get_thumbnail_for_image(document, size=320)
            except Exception:
                pass
            r = self.requests.get('sendDocument', params, files=files).json()
        return r

    def _send_video(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка видео. Ссылка или файл
        """
        params = copy(default_params)
        video: VideoAttachment = rmi.attachments[0]

        if video.file_id:
            params['video'] = video.file_id
            r = self.requests.get('sendVideo', params).json()
        elif video.public_download_url:
            params['video'] = video.public_download_url
            r = self.requests.get('sendVideo', params).json()
        else:
            if video.get_size_mb() > self.MAX_VIDEO_SIZE_MB:
                rmi.attachments = []
                raise PError(
                    f"Нельзя загружать видео более {self.MAX_VIDEO_SIZE_MB} мб в телеграмм. Ваше видео {round(video.get_size_mb(), 2)} мб")
            files = {'video': video.content}
            if video.thumb:
                thumb_file = self.get_photo_attachment(video.thumb, guarantee_url=True)
                files['thumbnail'] = thumb_file.get_bytes_io_content()
            r = self.requests.get('sendVideo', params, files=files).json()
        return r

    def _send_video_note(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка видео. Ссылка или файл
        """
        params = copy(default_params)
        video_note: VideoNoteAttachment = rmi.attachments[0]
        params['video_note'] = video_note.file_id
        r = self.requests.get('sendVideoNote', params).json()
        return r

    def _send_audio(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка аудио. Ссылка или файл
        """
        params = copy(default_params)
        audio: AudioAttachment = rmi.attachments[0]

        if audio.artist:
            params['performer'] = audio.artist
        if audio.title:
            params['title'] = audio.title

        if audio.public_download_url:
            params['audio'] = audio.public_download_url
            r = self.requests.get('sendAudio', params).json()
        else:
            files = {'audio': audio.content}
            if audio.thumb:
                thumb_file = self.get_photo_attachment(audio.thumb, guarantee_url=True)
                files['thumbnail'] = thumb_file.get_bytes_io_content()
            r = self.requests.get('sendAudio', params, files=files).json()
        return r

    def _send_gif(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка гифы. Ссылка или файл
        """
        params = copy(default_params)
        gif: GifAttachment = rmi.attachments[0]
        if gif.file_id:
            params['animation'] = gif.file_id
            r = self.requests.get('sendAnimation', params).json()
        elif gif.public_download_url:
            params['animation'] = gif.public_download_url
            r = self.requests.get('sendAnimation', params).json()
        else:
            if gif.get_size_mb() > self.MAX_GIF_SIZE:
                rmi.attachments = []
                raise PError(f"Нельзя загружать гифы более {self.MAX_GIF_SIZE} мб в телеграмм")
            r = self.requests.get('sendAnimation', params, files={'animation': gif.content}).json()
        return r

    def _send_sticker(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка стикера
        """
        params = copy(default_params)
        sticker: StickerAttachment = rmi.attachments[0]
        params['sticker'] = sticker.file_id
        r = self.requests.get('sendSticker', params).json()
        return r

    def _send_voice(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка голосовухи
        """
        params = copy(default_params)
        voice: VoiceAttachment = rmi.attachments[0]
        params['voice'] = voice.file_id
        r = self.requests.get('sendVoice', params).json()
        return r

    def _send_text(self, default_params) -> dict:
        params = copy(default_params)
        self.set_activity(params['chat_id'], ActivitiesEnum.TYPING)
        params['text'] = params.pop('caption')
        r = self.requests.get('sendMessage', params).json()
        return r

    def edit_message(self, default_params) -> dict:
        params = copy(default_params)
        params['text'] = params.pop('caption')
        r = self.requests.get('editMessageText', params=params).json()
        return r

    def edit_keyboard(self, default_params) -> dict:
        params = copy(default_params)
        del params['caption']
        r = self.requests.get('editMessageReplyMarkup', params=params).json()
        return r

    def edit_media(self, rm, default_params) -> dict:
        params = copy(default_params)
        att: Attachment = rm.attachments[0]
        params['media'] = {'type': att.type}
        if att.file_id:
            params['media']['media'] = att.file_id
        elif att.public_download_url:
            params['media']['media'] = att.public_download_url
        else:
            params['media']['media'] = self.get_file_id(att)
        params['media'] = json.dumps(params['media'])
        r = self.requests.get('editMessageMedia', params=params).json()
        return r

    def send_response_message_item(self, rmi: ResponseMessageItem) -> BotResponse:
        """
        Отправка ResponseMessageItem сообщения
        Возвращает {success:bool, response:Response.json()}
        """
        try:
            r = self._send_response_message_item(rmi)
        except (PWarning, PError) as e:
            error_rmi = ResponseMessageItem(
                text=e.msg,
                peer_id=rmi.peer_id,
                message_thread_id=rmi.message_thread_id,
                reply_to=e.reply_to,
                keyboard=e.keyboard
            )
            self.log_message(error_rmi, e.level)

            r = self._send_response_message_item(error_rmi)
            return BotResponse(False, r)
        finally:
            self.stop_activity_thread()

        if r['ok']:
            return BotResponse(True, r)

        # Непредвиденная ошибка телеги
        skip_errors = [
            "Bad Request: canceled by new editMessageMedia request",
            "Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message",
            "Forbidden: bot was blocked by the user",
            "Bad Request: message to edit not found",
        ]
        catch_errors = {
            'Bad Request: VOICE_MESSAGES_FORBIDDEN': "Не могу отправить голосовуху из-за ваших настроек безопасности",
            'Bad Request: failed to get HTTP URL content': "Ссылка не понравилась серверу телеграмм. Внутренняя ошибка.",
            'Bad Request: wrong file identifier/HTTP URL specified': "Ссылка не понравилась серверу телеграмм. Внутренняя ошибка."
        }
        error = r['description']
        if error in skip_errors:
            return BotResponse(False, r)
        elif error in catch_errors:
            msg = catch_errors[error]
            log_level = "warning"
        else:
            msg = self.ERROR_MSG
            log_level = "error"

        error_rmi = ResponseMessageItem(
            text=msg,
            peer_id=rmi.peer_id,
            message_thread_id=rmi.message_thread_id
        )
        self.log_message(error_rmi, log_level)

        try:
            r = self._send_response_message_item(error_rmi)
        finally:
            self.stop_activity_thread()

        return BotResponse(False, r)

    def _send_response_message_item(self, rmi: ResponseMessageItem) -> dict:
        """
        Отправка ResponseMessageItem сообщения
        Возвращает Response.json() платформы
        """
        rmi.set_telegram_html()
        params = {'chat_id': rmi.peer_id, 'caption': rmi.text}
        if rmi.keyboard:
            params['reply_markup'] = json.dumps(rmi.keyboard)
        params.update(rmi.kwargs)

        if rmi.reply_to:
            params['reply_to_message_id'] = rmi.reply_to
        if rmi.disable_web_page_preview:
            params['disable_web_page_preview'] = True
        if rmi.message_thread_id:
            params['message_thread_id'] = rmi.message_thread_id

        if rmi.message_id:
            params['message_id'] = rmi.message_id
            if rmi.attachments:
                return self.edit_media(rmi, params)
            if rmi.keyboard and not rmi.text:
                return self.edit_keyboard(params)
            return self.edit_message(params)

        # Разбиение длинных сообщений на чанки
        chunks = None
        if params.get('caption'):
            # Шлём длинные сообщения чанками.
            if rmi.attachments and len(params['caption']) > self.MAX_MESSAGE_TEXT_CAPTION:
                chunks = split_text_by_n_symbols(params['caption'], self.MAX_MESSAGE_TEXT_CAPTION)
                first_chunk = chunks[0]
                text = params['caption'][len(first_chunk):]
                chunks = split_text_by_n_symbols(text, self.MAX_MESSAGE_TEXT_LENGTH)
                chunks = [first_chunk] + chunks
                params['caption'] = chunks[0]
            elif len(params['caption']) > self.MAX_MESSAGE_TEXT_LENGTH:
                chunks = split_text_by_n_symbols(params['caption'], self.MAX_MESSAGE_TEXT_LENGTH)
                params['caption'] = chunks[0]

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

        if rmi.attachments:
            try:
                self.set_activity_thread(params['chat_id'], rmi.attachments[0].activity)
                # Отправка многих вложениями чанками: сначала вложения, потом текст
                if len(rmi.attachments) > 10:
                    rmi_copy = copy(rmi)
                    params_copy = copy(params)
                    params_copy['caption'] = ""
                    for chunk in get_chunks(rmi.attachments, 10):
                        rmi_copy.attachments = chunk
                        r = self._send_media_group(rmi_copy, params_copy)
                    if params['caption']:
                        r = self._send_text(params)
                elif len(rmi.attachments) > 1:
                    r = self._send_media_group(rmi, params)
                else:
                    r = att_map[rmi.attachments[0].__class__](rmi, params)
            finally:
                self.stop_activity_thread()
        else:
            r = self._send_text(params)

        # Отправка чанков отдельно. Последний чанк через return
        if chunks:
            for chunk in chunks[1:]:
                params['caption'] = chunk
                self._send_text(params)
        return r

    # END  MAIN ROUTING AND MESSAGING

    # LOGGING

    # END LOGGING

    # USERS GROUPS BOTS
    def update_profile_avatar(self, profile: Profile, user_id) -> dict:
        r = self.requests.get('getUserProfilePhotos', {'user_id': user_id}).json()
        photos = r['result']['photos']
        if len(photos) == 0:
            raise PWarning("Нет фотографий в профиле")
        pa = PhotoAttachment()
        pa.parse_tg(photos[0][-1])

        profile.set_avatar(pa)
        return r

    # END USERS GROUPS BOTS

    # EXTRA

    @staticmethod
    def get_button(text: str, command: str = None, args: list = None, kwargs: dict = None, url: str = None):
        callback_data = {}
        if command:
            callback_data["c"] = command
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
                {
                    'chat_id': peer_id,
                    'action': tg_activity
                }
            )
        ).start()

    def get_mention(self, profile: Profile, name=None):
        """
        Получение меншона пользователя
        """
        user = profile.get_tg_user()
        return self.get_formatted_url(str(profile), f"tg://user?id={user.user_id}")

    def delete_message(self, peer_id, message_id) -> dict:
        """
        Удаление одного сообщения
        """
        r = self.requests.get('deleteMessage', params={'chat_id': peer_id, 'message_id': message_id}).json()
        return r

    def update_help_texts(self):
        """
        Обновление списка команд в телеграме
        """

        from apps.bot.initial import COMMANDS
        commands_with_tg_name = list(filter(lambda x: x.name_tg, COMMANDS))
        help_texts_tg = [x.full_help_texts_tg.split(' - ') for x in commands_with_tg_name]
        help_texts_tg = [{'command': x[0], 'description': x[1]} for x in help_texts_tg]
        help_texts_tg.sort(key=lambda x: x['command'])
        r = self.requests.get('setMyCommands', json={'commands': help_texts_tg}).json()
        return r

    def get_sticker_set(self, name) -> list:
        r = self.requests.get('getStickerSet', json={'name': name}).json()
        return r['result']['stickers']

    def set_chat_admin_title(self, chat_id, user_id, title) -> dict:
        r = self.requests.get('setChatAdministratorCustomTitle', json={
            'chat_id': chat_id,
            'user_id': user_id,
            'custom_title': title
        }).json()
        return r

    def promote_chat_member(self, chat_id, user_id) -> dict:
        r = self.requests.get('promoteChatMember', json={
            'chat_id': chat_id,
            'user_id': user_id,
            'can_manage_chat': False,
            'can_pin_messages': True,
        }).json()
        return r

    def get_file_id(self, attachment):
        uploading_chat = Chat.objects.get(pk=env.str("TG_PHOTO_UPLOADING_CHAT_PK"))
        rmi = ResponseMessageItem(attachments=[attachment], peer_id=uploading_chat.chat_id)
        br = self.send_response_message_item(rmi)
        r = br.response
        self.delete_message(uploading_chat.chat_id, r['result']['message_id'])

        try:
            att = r['result'][attachment.type]
            if isinstance(att, list):
                att = att[0]
            file_id = att['file_id']
        except:
            raise PError()
        return file_id

    @classmethod
    def get_formatted_text(cls, text: str) -> str:
        """
        Форматированный текст
        """
        return f"<pre>{text.replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt;')}</pre>"

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
        return f'<tg-spoiler">{text}</tg-spoiler>'

    # END EXTRA

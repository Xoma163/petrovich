import json
import threading
from copy import copy
from math import inf

from apps.bot.consts import PlatformEnum
from apps.bot.core.bot.bot import Bot
from apps.bot.core.bot_response import BotResponse
from apps.bot.core.chat_action_sender import ChatActionSender
from apps.bot.core.chat_actions import ChatActionEnum, TG_CHAT_ACTIONS
from apps.bot.core.connectors.telegram.telegram import TelegramAPI, TelegramAPIRequestMode
from apps.bot.core.event.event import Event
from apps.bot.core.event.telegram.tg_event import TgEvent
from apps.bot.core.messages.attachments.attachment import Attachment
from apps.bot.core.messages.attachments.audio import AudioAttachment
from apps.bot.core.messages.attachments.document import DocumentAttachment
from apps.bot.core.messages.attachments.gif import GifAttachment
from apps.bot.core.messages.attachments.photo import PhotoAttachment
from apps.bot.core.messages.attachments.sticker import StickerAttachment
from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.bot.core.messages.attachments.video_note import VideoNoteAttachment
from apps.bot.core.messages.attachments.voice import VoiceAttachment
from apps.bot.core.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.models import Profile, Chat
from apps.commands.meme.commands.meme import Meme
from apps.shared.exceptions import PError, PWarning, PSkip
from apps.shared.utils.utils import split_text_by_n_symbols, get_chunks
from petrovich.settings import env


class TgBot(Bot):
    CODE_TAG = "code"
    PRE_TAG = "pre"
    SPOILER_TAG = "tg-spoiler"
    BOLD_TAG = "b"
    ITALIC_TAG = "i"
    LINK_TAG = "a"
    STROKE_TAG = "s"
    UNDERLINE_TAG = "u"
    QUOTE_TAG = "blockquote"

    @property
    def max_video_size_mb(self):
        return 50 if self.api_handler.is_tg_server_mode else 2000

    @property
    def max_photo_size_mb(self):
        return 5 if self.api_handler.is_tg_server_mode else inf

    @property
    def max_attachment_size_mb(self):
        return 20 if self.api_handler.is_tg_server_mode else inf

    @property
    def max_gif_size_mb(self):
        return 40 if self.api_handler.is_tg_server_mode else inf

    @property
    def max_message_text_length(self):
        return 4096

    @property
    def max_message_caption_length(self):
        return 1024

    @property
    def max_thumbnail_size(self):
        return 320

    def __init__(self):
        Bot.__init__(self, PlatformEnum.TG)
        self.api_handler = TelegramAPI(env.str("TG_TOKEN"), TelegramAPIRequestMode.LOCAL_SERVER)

        self.att_map = {
            PhotoAttachment: self._send_photo,
            GifAttachment: self._send_gif,
            VideoAttachment: self._send_video,
            VideoNoteAttachment: self._send_video_note,
            AudioAttachment: self._send_audio,
            DocumentAttachment: self._send_document,
            StickerAttachment: self._send_sticker,
            VoiceAttachment: self._send_voice,
        }

    # MAIN ROUTING AND MESSAGING

    def parse(self, raw_event):
        """
        Точка входа. Сюда попадает raw json event
        """
        tg_event = TgEvent(raw_event)
        threading.Thread(target=self.handle_event, args=(tg_event,)).start()

    def route(self, event: Event) -> ResponseMessage:
        if isinstance(event, TgEvent) and event.inline_mode:
            self.route_inline_mode(event)
            raise PSkip()

        return super().route(event)

    def route_inline_mode(self, event) -> dict:
        """
        Режим работы исключительно для поиска мемасов
        """
        data = event.inline_data

        filter_list = event.inline_data['message'].clear.split(' ')
        filter_list = filter_list if filter_list[0] else []

        meme_cmd = Meme(self, event)
        inline_query_result = meme_cmd.get_tg_inline_memes(filter_list)

        return self.api_handler.answer_inline_query(
            inline_query_id=data['id'],
            results=inline_query_result,
            cache_time=0
        )

    def _send_media_group_wrap(self, rmi: ResponseMessageItem, default_params) -> dict:
        params = copy(default_params)
        params.pop('parse_mode')  # Не поддерживается телегой
        caption = params.pop('caption')

        media_list = []
        files = []
        for i, attachment in enumerate(rmi.attachments):
            if attachment.file_id:
                media = {'type': attachment.type, 'media': attachment.file_id}
            elif attachment.public_download_url and not attachment.content:
                media = {'type': attachment.type, 'media': attachment.public_download_url}
            else:
                filename = attachment.file_name if attachment.file_name else str(i)
                # files.append(attachment.get_bytes_io_content())
                files.append((filename, attachment.content))
                media = {'type': attachment.type, "media": f"attach://{filename}"}

            if getattr(attachment, 'artist', None):
                media['performer'] = attachment.artist
            if getattr(attachment, 'title', None):
                media['title'] = attachment.title
            if getattr(attachment, 'set_thumbnail', None):
                attachment.set_thumbnail()
            if getattr(attachment, 'thumbnail', None):
                thumb_file = attachment.thumbnail
                thumb_filename = f"thumb_{str(i)}"
                files.append((thumb_filename, thumb_file.get_bytes_io_content()))
                media['thumbnail'] = f"attach://{thumb_filename}"

            media_list.append(media)

        media_list[-1]['caption'] = caption

        params['media'] = media_list
        return self.api_handler.send_media_group(**params, files=files)

    def _send_media_group(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка множества вложений. Ссылки
        """

        responses = []
        r = None
        # Бьём на чанки если вложений больше 10
        if len(rmi.attachments) > 10:
            rmi_copy = copy(rmi)
            params_copy = copy(default_params)
            params_copy['caption'] = ""
            for chunk in get_chunks(rmi.attachments, 10):
                rmi_copy.attachments = chunk
                r = self._send_media_group_wrap(rmi_copy, params_copy)
                responses.append(r)
            if default_params['caption']:
                self._send_text(default_params)
        # Отправка одного
        else:
            r = self._send_media_group_wrap(rmi, default_params)
            responses.append(r)

        # Если не получилось отправить media_group, то пытаемся отправить вложения по одному
        for response in responses:
            if response['ok']:
                continue
            rmi_copy = copy(rmi)
            params_copy = copy(default_params)
            params_copy['caption'] = ""
            for chunk in get_chunks(rmi.attachments, 1):
                rmi_copy.attachments = chunk
                r = self._send_media_group_wrap(rmi_copy, params_copy)
        return r

    def _send_photo(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка фото. Ссылка или файл
        """

        params = copy(default_params)
        photo: PhotoAttachment = rmi.attachments[0]
        files = None
        if rmi.spoiler:
            params['has_spoiler'] = rmi.spoiler
        if photo.file_id:
            params['photo'] = photo.file_id
        elif photo.public_download_url and not photo.content:
            params['photo'] = photo.public_download_url
        else:
            if photo.get_size_mb() > self.max_photo_size_mb:
                rmi.attachments = []
                raise PError(f"Нельзя загружать фото более {self.max_photo_size_mb} мб в телеграмм")
            files = {'photo': photo.get_bytes_io_content()}
        return self.api_handler.send_photo(**params, files=files)

    def _send_document(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка документа. Ссылка или файл
        """
        params = copy(default_params)
        document: DocumentAttachment = rmi.attachments[0]
        files = None
        if document.file_id:
            params['document'] = document.file_id
        elif document.public_download_url and not document.content:
            params['document'] = document.public_download_url
        else:
            files = {'document': document.get_bytes_io_content()}
            document.set_thumbnail()
            if document.thumbnail:
                files['thumbnail'] = document.thumbnail.get_bytes_io_content()

        return self.api_handler.send_document(**params, files=files)

    def _send_video(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка видео. Ссылка или файл
        """
        params = copy(default_params)

        video: VideoAttachment = rmi.attachments[0]
        files = None
        if video.width:
            params['width'] = video.width
        if video.height:
            params['height'] = video.height
        if rmi.spoiler:
            params['has_spoiler'] = rmi.spoiler

        if video.file_id:
            params['video'] = video.file_id
        elif video.public_download_url and not video.content:
            params['video'] = video.public_download_url
        else:
            if video.get_size_mb() > self.max_video_size_mb:
                rmi.attachments = []
                raise PError(
                    f"Нельзя загружать видео более {self.max_video_size_mb} мб в телеграмм. Ваше видео {round(video.get_size_mb(), 2)} мб")
            with ChatActionSender(self, ChatActionEnum.UPLOAD_VIDEO, params['chat_id'],
                                  params.get('message_thread_id')):
                files = {'video': video.get_bytes_io_content()}
                video.set_thumbnail()
                if video.thumbnail:
                    files['thumbnail'] = video.thumbnail.get_bytes_io_content()
        return self.api_handler.send_video(**params, files=files)

    def _send_video_note(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка видео. Ссылка или файл
        """
        params = copy(default_params)
        params.pop('parse_mode')  # Не поддерживается телегой

        video_note: VideoNoteAttachment = rmi.attachments[0]
        params['video_note'] = video_note.file_id
        return self.api_handler.send_video_note(**params).json()

    def _send_audio(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка аудио. Ссылка или файл
        """
        params = copy(default_params)
        audio: AudioAttachment = rmi.attachments[0]
        files = None

        if audio.artist:
            params['performer'] = audio.artist
        if audio.title:
            params['title'] = audio.title

        # Через public url плохо работает - не тянется название и thumbnail
        if audio.public_download_url:
            if audio.thumbnail_url:
                params['thumbnail'] = audio.thumbnail_url
            params['audio'] = audio.public_download_url
        else:
            files = {'audio': audio.get_bytes_io_content()}
            audio.set_thumbnail()
            if audio.thumbnail:
                files['thumbnail'] = audio.thumbnail.get_bytes_io_content()
        return self.api_handler.send_audio(**params, files=files)

    def _send_gif(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка гифы. Ссылка или файл
        """
        params = copy(default_params)
        gif: GifAttachment = rmi.attachments[0]
        files = None
        if rmi.spoiler:
            params['has_spoiler'] = rmi.spoiler
        if gif.file_id:
            params['animation'] = gif.file_id
        elif gif.public_download_url:
            params['animation'] = gif.public_download_url
        else:
            if gif.get_size_mb() > self.max_gif_size_mb:
                rmi.attachments = []
                raise PError(f"Нельзя загружать гифы более {self.max_gif_size_mb} мб в телеграмм")
            files = gif.get_bytes_io_content()
        return self.api_handler.send_animation(**params, files=files)

    def _send_sticker(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка стикера
        """
        params = copy(default_params)
        params.pop('parse_mode')  # Не поддерживается телегой

        sticker: StickerAttachment = rmi.attachments[0]
        params['sticker'] = sticker.file_id
        return self.api_handler.send_sticker(**params)

    def _send_voice(self, rmi: ResponseMessageItem, default_params) -> dict:
        """
        Отправка голосовухи
        """
        params = copy(default_params)
        voice: VoiceAttachment = rmi.attachments[0]
        params['voice'] = voice.file_id
        return self.api_handler.send_voice(**params)

    def _send_text(self, default_params) -> dict:
        params = copy(default_params)
        return self.api_handler.send_message(**params)

    def edit_message(self, default_params) -> dict:
        params = copy(default_params)
        return self.api_handler.edit_message_text(**params)

    def edit_caption(self, default_params) -> dict:
        params = copy(default_params)
        return self.api_handler.edit_message_caption(**params)

    def edit_keyboard(self, default_params) -> dict:
        params = copy(default_params)
        return self.api_handler.edit_messaage_reply_markup(**params)

    def edit_media(self, rmi: ResponseMessageItem, default_params) -> dict:
        params = copy(default_params)
        att: Attachment = rmi.attachments[0]
        params['media'] = {'type': att.type}
        if att.file_id:
            params['media']['media'] = att.file_id
        elif att.public_download_url:
            params['media']['media'] = att.public_download_url
        else:
            params['media']['media'] = self.get_file_id(att)
        return self.api_handler.edit_message_media(**params)

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

        if r['ok']:
            return BotResponse(True, r)

        # Непредвиденная ошибка телеги
        skip_errors = [
            "Bad Request: canceled by new editMessageMedia request",
            "Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message",
            "Forbidden: bot was blocked by the user",
            "Bad Request: message to edit not found",
            "Bad Request: message can't be deleted",
            "Bad Request: message can't be deleted for everyone"
        ]
        BAD_URL_ERROR_MSG = "Ссылка не понравилась серверу телеграмм. Внутренняя ошибка."
        bad_url_catch_errors = {
            'Bad Request: failed to get HTTP URL content': BAD_URL_ERROR_MSG,
            'Bad Request: wrong file identifier/HTTP URL specified': BAD_URL_ERROR_MSG,
            'Bad Request: wrong type of the web page content': BAD_URL_ERROR_MSG
        }
        catch_errors = {
            'Bad Request: VOICE_MESSAGES_FORBIDDEN': "Не могу отправить голосовуху из-за ваших настроек безопасности",
        }
        catch_errors_starts_with = {
            "Bad Request: can't parse entities": "Не смог распарсить markdown/html сущности. Внутренняя ошибка."
        }

        error = r['description']

        catch_errors_start_error = None
        for key in catch_errors_starts_with:
            if key in error:
                catch_errors_start_error = catch_errors_starts_with[key]
                break

        if error in skip_errors:
            return BotResponse(False, r)
        elif catch_errors_start_error:
            msg = catch_errors_start_error
            log_level = "warning"
        elif error in bad_url_catch_errors:
            msg = bad_url_catch_errors[error]
            log_level = "warning"

            links_str = []
            for i, att in enumerate(rmi.attachments):
                link = att.public_download_url
                link_str = self.get_formatted_url(f"Ссылка #{i + 1}", link)
                links_str.append(link_str)
            links_str = "\n".join(links_str)
            msg = f"{msg}\n\n{links_str}"
            if rmi.text:
                msg = f"{msg}\n\n{rmi.text}"
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
        r = self._send_response_message_item(error_rmi)
        return BotResponse(False, r)

    def _send_response_message_item(self, rmi: ResponseMessageItem) -> dict:
        """
        Отправка ResponseMessageItem сообщения
        Возвращает Response.json() платформы
        """
        rmi.set_telegram_html()

        params = rmi.get_tg_params()

        if rmi.message_id:
            if rmi.attachments:
                return self.edit_media(rmi, params)
            if rmi.keyboard and not rmi.text:
                return self.edit_keyboard(params)
            return self.edit_message(params)

        # Разбиение длинных сообщений на чанки
        chunks = self._get_text_chunks(rmi, params)

        if rmi.attachments:
            with ChatActionSender(self, rmi.attachments[0].ACTION, rmi.peer_id, rmi.message_thread_id):
                # Отправка многих вложениями чанками: сначала вложения, потом текст
                if len(rmi.attachments) > 1:
                    r = self._send_media_group(rmi, params)
                else:
                    r = self.att_map[rmi.attachments[0].__class__](rmi, params)  # noqa
        else:
            r = self._send_text(params)

        # Отправка чанков отдельно
        if chunks:
            params.pop('caption')
            for chunk in chunks[1:]:
                params['text'] = chunk
                self._send_text(params)
        return r

    def _get_text_chunks(self, rmi, params) -> list | None:
        """
        Разбивка сообщения на чанки
        """

        chunks = None
        if not params.get('caption'):
            return chunks

        # Если у нас есть форматирование, в таком случае все сначала шлём все медиа, а потом уже форматированный текст
        # Телега не умеет в send_media_group + parse_mode
        if rmi.parse_mode and len(rmi.attachments) > 1:
            chunks = [""] + split_text_by_n_symbols(params['caption'], self.max_message_text_length)
            params['caption'] = chunks[0]

        # Шлём длинные сообщения чанками.
        if rmi.attachments and len(params['caption']) > self.max_message_caption_length:
            # Иначё бьём на 1024 символа первое сообщение и на 4096 остальные (ограничения телеги)
            chunks = split_text_by_n_symbols(params['caption'], self.max_message_caption_length)
            first_chunk = chunks[0]
            text = params['caption'][len(first_chunk):]
            chunks = split_text_by_n_symbols(text, self.max_message_text_length)
            chunks = [first_chunk] + chunks
            params['caption'] = chunks[0]
        # Обычные длинные текстовые сообщения шлём чанками
        elif len(params['caption']) > self.max_message_text_length:
            chunks = split_text_by_n_symbols(params['caption'], self.max_message_text_length)
            params['caption'] = chunks[0]

        return chunks

    # END  MAIN ROUTING AND MESSAGING

    # LOGGING

    # END LOGGING

    # USERS GROUPS BOTS
    def get_user_profile_photos(self, user_id: int | str) -> dict:
        r = self.api_handler.get_user_profile_photos(user_id)
        return r['result']['photos']

    def get_chat_administrators(self, chat_id: int | str) -> dict:
        return self.api_handler.get_chat_administrators(chat_id)['result']

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

    @staticmethod
    def get_inline_keyboard(buttons: list, cols=1):
        """
        param buttons: ToDo:
        Получение инлайн-клавиатуры с кнопками
        В основном используется для команд, где нужно запускать много команд и лень набирать заново
        """
        buttons_chunks = get_chunks(buttons, cols)
        keyboard = list(buttons_chunks)
        return {
            'inline_keyboard': keyboard
        }

    def set_chat_action(self, chat_id: int | str, chat_action: ChatActionEnum, message_thread_id: int | None = None):
        """
        Метод позволяет указать пользователю, что бот набирает сообщение или записывает голосовое
        Используется при длительном выполнении команд, чтобы был фидбек пользователю, что его запрос принят
        """
        tg_chat_action = TG_CHAT_ACTIONS[chat_action]

        # no wait for response
        threading.Thread(
            target=self.api_handler.send_chat_action,
            args=(
                chat_id,
                tg_chat_action,
                message_thread_id
            )
        ).start()

    def get_mention(self, profile: Profile) -> str:
        """
        Получение меншона пользователя
        """
        user = profile.get_tg_user()
        if profile.settings.use_mention:
            return self.get_formatted_url(str(profile), f"tg://user?id={user.user_id}")
        return super().get_mention(profile)

    def delete_messages(self, chat_id: int | str, message_ids: list[int] | int) -> dict:
        """
        Удаление одного сообщения
        """
        if not isinstance(message_ids, list):
            message_ids = [message_ids]
        return self.api_handler.delete_messages(chat_id, message_ids)

    def leave_chat(self, chat_id) -> dict:
        return self.api_handler.leave_chat(chat_id)

    def get_file_id(self, attachment: Attachment):
        uploading_chat = Chat.objects.get(pk=env.str("TG_PHOTO_UPLOADING_CHAT_PK"))
        rmi = ResponseMessageItem(attachments=[attachment], peer_id=int(uploading_chat.chat_id))
        br = self.send_response_message_item(rmi)
        r = br.response
        self.delete_messages(uploading_chat.chat_id, r['result']['message_id'])

        try:
            att = r['result'][attachment.type]
            if isinstance(att, list):
                att = att[0]
            file_id = att['file_id']
        except Exception:
            raise PError()
        return file_id

    def answer_callback_query(self, callback_query_id: int) -> dict:
        return self.api_handler.answer_callback_query(callback_query_id)

    @classmethod
    def get_formatted_text(cls, text: str, language: str = None) -> str:
        """
        Форматированный текст
        """
        if language:
            pre_inner = f"<{cls.CODE_TAG} class='language-{language}'>{text}</{cls.CODE_TAG}>"
        else:
            pre_inner = text
        return f"<{cls.PRE_TAG}>{pre_inner}</{cls.PRE_TAG}>"

    @classmethod
    def get_formatted_text_line(cls, text: str) -> str:
        """
        Форматированный текст в одну линию
        """
        return f"<{cls.CODE_TAG}>{text}</{cls.CODE_TAG}>"

    @classmethod
    def get_formatted_url(cls, name: str, url: str) -> str:
        return f'<{cls.LINK_TAG} href="{url}">{name}</{cls.LINK_TAG}>'

    @classmethod
    def get_underline_text(cls, text: str) -> str:
        """
        Текст с нижним подчёркиванием
        """
        return f"<{cls.UNDERLINE_TAG}>{text}</{cls.UNDERLINE_TAG}>"

    @classmethod
    def get_italic_text(cls, text: str) -> str:
        """
        Наклонный текст
        """
        return f"<{cls.ITALIC_TAG}>{text}</{cls.ITALIC_TAG}>"

    @classmethod
    def get_bold_text(cls, text: str) -> str:
        """
        Жирный текст
        """
        return f"<{cls.BOLD_TAG}>{text}</{cls.BOLD_TAG}>"

    @classmethod
    def get_strike_text(cls, text: str) -> str:
        """
        Зачёрнутый текст
        """
        return f"<{cls.STROKE_TAG}>{text}</{cls.STROKE_TAG}>"

    @classmethod
    def get_spoiler_text(cls, text: str) -> str:
        """
        Спойлер-текст
        """
        return f'<{cls.SPOILER_TAG}>{text}</{cls.SPOILER_TAG}>'

    @classmethod
    def get_quote_text(cls, text: str, expandable: bool = False) -> str:
        """
        Цитата текст
        """
        expandable = " expandable" if expandable else ""
        return f'<{cls.QUOTE_TAG}{expandable}>{text}</{cls.QUOTE_TAG}>'

    # END EXTRA

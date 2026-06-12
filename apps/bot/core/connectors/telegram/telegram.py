import json
from enum import Enum
from typing import Any

from apps.bot.core.connectors.telegram.request import Request, RequestLocal

TelegramResponse = dict[str, Any]
TelegramFiles = dict[str, Any]
TelegramMedia = list[dict[str, Any]]


class TelegramAPIRequestMode(Enum):
    TG_SERVER = 0
    LOCAL_SERVER = 1


class TelegramAPI:
    @property
    def is_tg_server_mode(self):
        return self.mode == TelegramAPIRequestMode.TG_SERVER

    @property
    def is_local_server_mode(self):
        return self.mode == TelegramAPIRequestMode.LOCAL_SERVER

    def __init__(self, token, mode: TelegramAPIRequestMode, log_filter=None):
        self.token = token
        self.mode = mode
        self.log_filter = log_filter

        self.requests: Request = self._init_requests()

    def _init_requests(self) -> Request:
        if self.mode == TelegramAPIRequestMode.TG_SERVER:
            return Request(self.token, log_filter=self.log_filter)
        if self.mode == TelegramAPIRequestMode.LOCAL_SERVER:
            return RequestLocal(self.token, log_filter=self.log_filter)
        raise RuntimeError(f"{self.mode} is not supported")

    def get_updates(
        self,
        offset: int | None = None,
        limit: int | None = None,
        timeout: int | None = None,
        allowed_updates: list[str] | None = None,
    ) -> TelegramResponse:
        params: dict[str, object] = {
            "offset": offset,
            "limit": limit,
            "timeout": timeout,
        }
        if allowed_updates:
            params["allowed_updates"] = json.dumps(allowed_updates)

        return self.requests.post("getUpdates", params).json()

    def delete_webhook(self, drop_pending_updates: bool = False) -> TelegramResponse:
        params: dict[str, object] = {"drop_pending_updates": drop_pending_updates}
        return self.requests.post("deleteWebhook", params).json()

    # ---------- SEND --------- #

    def send_chat_action(self, chat_id: int | str, action: str, message_thread_id: int = None) -> TelegramResponse:
        params: dict[str, object] = {"chat_id": chat_id, "message_thread_id": message_thread_id, "action": action}
        return self.requests.post("sendChatAction", params).json()

    def send_message(
        self,
        chat_id: int | str,
        text: str | None,
        message_thread_id: int = None,
        reply_to_message_id: int = None,
        parse_mode: str = None,
        reply_markup: dict = None,
        disable_web_page_preview: bool = None,
        entities: list = None,
    ) -> TelegramResponse:
        params: dict[str, object] = {
            "chat_id": chat_id,
            "message_thread_id": message_thread_id,
            "reply_to_message_id": reply_to_message_id,
            "parse_mode": parse_mode,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)
        if entities:
            params["reply_markup"] = json.dumps(entities)

        return self.requests.post("sendMessage", params).json()

    def send_message_draft(
        self,
        chat_id: int | str,
        draft_id: int,
        text: str | None,
        message_thread_id: int = None,
        parse_mode: str = None,
    ) -> TelegramResponse:
        params: dict[str, object] = {
            "chat_id": chat_id,
            "draft_id": draft_id,
            "text": text,
            "message_thread_id": message_thread_id,
            "parse_mode": parse_mode,
        }

        return self.requests.post("sendMessageDraft", params).json()

    def send_rich_message(
        self,
        chat_id: int | str,
        rich_message: dict,
        message_thread_id: int = None,
        reply_to_message_id: int = None,
        reply_markup: dict = None,
    ) -> TelegramResponse:
        params: dict[str, object] = {
            "chat_id": chat_id,
            "message_thread_id": message_thread_id,
            "rich_message": json.dumps(rich_message),
        }
        if reply_to_message_id:
            params["reply_parameters"] = json.dumps({"message_id": reply_to_message_id})
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)

        return self.requests.post("sendRichMessage", params).json()

    def send_rich_message_draft(
        self,
        chat_id: int | str,
        draft_id: int,
        rich_message: dict,
        message_thread_id: int = None,
    ) -> TelegramResponse:
        params: dict[str, object] = {
            "chat_id": chat_id,
            "draft_id": draft_id,
            "rich_message": json.dumps(rich_message),
            "message_thread_id": message_thread_id,
        }

        return self.requests.post("sendRichMessageDraft", params).json()

    def send_media_group(
        self,
        chat_id: int | str,
        message_thread_id: int = None,
        reply_to_message_id: int = None,
        media: TelegramMedia | None = None,
        files: list[tuple[str, Any]] | None = None,
    ) -> TelegramResponse:
        if not media and not files:
            raise ValueError("media or files must be provided")
        params: dict[str, object] = {
            "chat_id": chat_id,
            "message_thread_id": message_thread_id,
            "reply_to_message_id": reply_to_message_id,
        }
        if media:
            params["media"] = json.dumps(media)  # noqa

        return self.requests.post("sendMediaGroup", params, files=files).json()

    def send_photo(
        self,
        chat_id: int | str,
        message_thread_id: int = None,
        reply_to_message_id: int = None,
        reply_markup: dict = None,
        parse_mode: str = None,
        caption: str = None,
        has_spoiler: bool = None,
        photo: str = None,
        files: TelegramFiles | None = None,
    ) -> TelegramResponse:
        if not photo and not files:
            raise ValueError('photo or files["photo"] must be provided')
        params: dict[str, object] = {
            "chat_id": chat_id,
            "message_thread_id": message_thread_id,
            "reply_to_message_id": reply_to_message_id,
            "parse_mode": parse_mode,
            "caption": caption,
            "has_spoiler": has_spoiler,
            "photo": photo,
        }
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)

        return self.requests.post("sendPhoto", params, files=files).json()

    def send_document(
        self,
        chat_id: int | str,
        message_thread_id: int = None,
        reply_to_message_id: int = None,
        reply_markup: dict = None,
        parse_mode: str = None,
        caption: str = None,
        document: str = None,
        files: TelegramFiles | None = None,
    ) -> TelegramResponse:
        if not document and not files:
            raise ValueError('document or files["document"] must be provided')
        params: dict[str, object] = {
            "chat_id": chat_id,
            "message_thread_id": message_thread_id,
            "reply_to_message_id": reply_to_message_id,
            "parse_mode": parse_mode,
            "caption": caption,
            "document": document,
        }
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)

        return self.requests.post("sendDocument", params, files=files).json()

    def send_video(
        self,
        chat_id: int | str,
        message_thread_id: int = None,
        reply_to_message_id: int = None,
        reply_markup: dict = None,
        parse_mode: str = None,
        caption: str = None,
        width: int = None,
        height: int = None,
        has_spoiler: bool = None,
        video: str = None,
        files: TelegramFiles | None = None,
    ) -> TelegramResponse:
        if not video and not files:
            raise ValueError('video or files["video"] must be provided')

        params: dict[str, object] = {
            "chat_id": chat_id,
            "message_thread_id": message_thread_id,
            "reply_to_message_id": reply_to_message_id,
            "parse_mode": parse_mode,
            "caption": caption,
            "width": width,
            "height": height,
            "has_spoiler": has_spoiler,
            "video": video,
        }
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)  # noqa
        return self.requests.post("sendVideo", params, files=files).json()

    def send_video_note(
        self,
        chat_id: int | str,
        message_thread_id: int = None,
        reply_to_message_id: int = None,
        reply_markup: dict = None,
        video_note: str = None,
        files: TelegramFiles | None = None,
    ) -> TelegramResponse:
        if not video_note and not files:
            raise ValueError('video_note or files["video_note"] must be provided')

        params: dict[str, object] = {
            "chat_id": chat_id,
            "message_thread_id": message_thread_id,
            "reply_to_message_id": reply_to_message_id,
            "video_note": video_note,
        }
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)

        return self.requests.post("sendVideoNote", params, files=files).json()

    def send_audio(
        self,
        chat_id: int | str,
        message_thread_id: int = None,
        reply_to_message_id: int = None,
        reply_markup: dict = None,
        parse_mode: str = None,
        caption: str = None,
        title: str = None,
        duration: int = None,
        performer: str = None,
        audio: str = None,
        thumbnail: str = None,
        files: TelegramFiles | None = None,
    ) -> TelegramResponse:
        if not audio and not files:
            raise ValueError('audio or files["audio"] must be provided')

        params: dict[str, object] = {
            "chat_id": chat_id,
            "message_thread_id": message_thread_id,
            "reply_to_message_id": reply_to_message_id,
            "parse_mode": parse_mode,
            "caption": caption,
            "title": title,
            "duration": duration,
            "performer": performer,
            "audio": audio,
            "thumbnail": thumbnail,
        }
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)

        return self.requests.post("sendAudio", params, files=files).json()

    def send_animation(
        self,
        chat_id: int | str,
        message_thread_id: int = None,
        reply_to_message_id: int = None,
        reply_markup: dict = None,
        parse_mode: str = None,
        caption: str = None,
        has_spoiler: bool = None,
        animation: str = None,
        files: TelegramFiles | None = None,
    ) -> TelegramResponse:
        if not animation and not files:
            raise ValueError('animation or files["animation"] must be provided')
        params: dict[str, object] = {
            "chat_id": chat_id,
            "message_thread_id": message_thread_id,
            "reply_to_message_id": reply_to_message_id,
            "parse_mode": parse_mode,
            "caption": caption,
            "has_spoiler": has_spoiler,
            "animation": animation,
        }
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)

        return self.requests.post("sendAnimation", params, files=files).json()

    def send_sticker(
        self,
        chat_id: int | str,
        message_thread_id: int = None,
        reply_to_message_id: int = None,
        reply_markup: dict = None,
        sticker: str = None,
        files: TelegramFiles | None = None,
    ) -> TelegramResponse:
        if not sticker and not files:
            raise ValueError('sticker or files["sticker"] must be provided')
        params: dict[str, object] = {
            "chat_id": chat_id,
            "message_thread_id": message_thread_id,
            "reply_to_message_id": reply_to_message_id,
            "sticker": sticker,
        }
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)

        return self.requests.post("sendSticker", params).json()

    def send_voice(
        self,
        chat_id: int | str,
        message_thread_id: int = None,
        reply_to_message_id: int = None,
        reply_markup: dict = None,
        parse_mode: str = None,
        voice: str = None,
        files: TelegramFiles | None = None,
    ) -> TelegramResponse:
        if not voice and not files:
            raise ValueError('voice or files["voice"] must be provided')
        params: dict[str, object] = {
            "chat_id": chat_id,
            "message_thread_id": message_thread_id,
            "reply_to_message_id": reply_to_message_id,
            "parse_mode": parse_mode,
            "voice": voice,
        }
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)

        return self.requests.post("sendVoice", params).json()

    # ---------- EDIT --------- #

    def edit_message_text(
        self,
        chat_id: int | str,
        message_id: int | None,
        text: str | None,
        reply_markup: dict = None,
        parse_mode: str = None,
        rich_message: dict | None = None,
    ) -> TelegramResponse:
        params: dict[str, object] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        if rich_message:
            params["rich_message"] = json.dumps(rich_message)
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)

        return self.requests.post("editMessageText", params).json()

    def edit_message_caption(
        self,
        chat_id: int | str,
        message_id: int | None,
        caption: str | None,
        reply_markup: dict = None,
        parse_mode: str = None,
    ) -> TelegramResponse:
        params: dict[str, object] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "caption": caption,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)

        return self.requests.post("editMessageCaption", params).json()

    def edit_messaage_reply_markup(
        self, chat_id: int | str, message_id: int | None, reply_markup: dict | None
    ) -> TelegramResponse:
        params: dict[str, object] = {
            "chat_id": chat_id,
            "message_id": message_id,
        }
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)  # noqa

        return self.requests.post("editMessageReplyMarkup", params=params).json()

    def edit_message_media(self, chat_id: int | str, message_id: int | None, media: dict[str, Any]) -> TelegramResponse:
        params: dict[str, object] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "media": json.dumps(media),
        }

        return self.requests.post("editMessageMedia", params=params).json()

    # ---------- DELETE --------- #

    def delete_messages(self, chat_id: int | str, message_ids: list[int]) -> TelegramResponse:
        """
        Удаление сообщений
        """
        params: dict[str, object] = {"chat_id": chat_id, "message_ids": json.dumps(message_ids)}
        return self.requests.post("deleteMessages", params=params).json()

    # ---------- CHAT --------- #

    def get_chat_administrators(self, chat_id: int | str) -> TelegramResponse:
        params: dict[str, object] = {
            "chat_id": chat_id,
        }
        return self.requests.post("getChatAdministrators", params).json()

    def leave_chat(self, chat_id: int | str) -> TelegramResponse:
        params: dict[str, object] = {
            "chat_id": chat_id,
        }
        return self.requests.post("leaveChat", params).json()

    # ---------- USER --------- #

    def get_user_profile_photos(self, user_id: int) -> TelegramResponse:
        params: dict[str, object] = {
            "user_id": user_id,
        }
        return self.requests.post("getUserProfilePhotos", params=params).json()

    # ---------- FILE --------- #

    def get_file(self, file_id: str) -> TelegramResponse:
        params: dict[str, object] = {
            "file_id": file_id,
        }
        return self.requests.post("getFile", params=params).json()

    # ---------- OTHER --------- #

    def answer_inline_query(
        self, inline_query_id: str, results: list[dict[str, Any]], cache_time: int
    ) -> TelegramResponse:
        params: dict[str, object] = {
            "inline_query_id": inline_query_id,
            "results": json.dumps(results, ensure_ascii=False),
            "cache_time": cache_time,
        }

        return self.requests.post("answerInlineQuery", params).json()

    def answer_callback_query(self, callback_query_id: str) -> TelegramResponse:
        params: dict[str, object] = {
            "callback_query_id": callback_query_id,
        }
        return self.requests.post("answerCallbackQuery", params).json()

    # ---------- NO API --------- #

    def get_file_download_url(self, file_path: str):
        return f"{self.requests.PREFIX}://{self.requests.API_TELEGRAM_URL}/file/bot{self.token}/{file_path}"

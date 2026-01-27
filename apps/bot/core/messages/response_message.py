import json
import re
from copy import copy

from apps.bot.core.messages.telegram.parse_mode import TelegramParseMode


class ResponseMessageItem:
    TG_TAGS = ['pre', 'code', 'tg-spoiler', 'i', 'b', 'u', 'a', 's', 'blockquote']

    URLS_REGEXP = r"(http|ftp|https|tg)(:\/\/)([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])"

    def __init__(
            self,
            text: str | None = None,
            attachments: list | None = None,
            reply_to: str | None = None,
            keyboard: dict | None = None,
            message_id: str | None = None,
            message_thread_id: str | int | None = None,
            peer_id: int | None = None,
            log_level: str = 'debug',
            exc_info=None,
            disable_web_page_preview: bool = False,
            entities: list | None = None,
            send: bool = True,
            spoiler: bool = False,
            parse_mode: TelegramParseMode | None = None
    ):
        self.text = text
        self.attachments = attachments if attachments else []
        if not isinstance(self.attachments, list):
            self.attachments = [self.attachments]
        self.reply_to = reply_to
        self.keyboard = keyboard
        self.message_id = message_id
        self.message_thread_id = message_thread_id
        self.peer_id = peer_id

        self.log_level = log_level
        self.exc_info = exc_info

        self.disable_web_page_preview = disable_web_page_preview
        self.entities = entities

        self.kwargs = {}

        self.send = send
        self.spoiler = spoiler
        self.parse_mode = parse_mode

    def to_log(self) -> dict:
        """
        Вывод в логи
        """
        dict_self = copy(self.__dict__)
        ignore_fields = ['log_level', 'exc_info']
        for ignore_field in ignore_fields:
            del dict_self[ignore_field]

        dict_self["attachments"] = [x.to_log() for x in dict_self["attachments"]]
        return dict_self

    def to_api(self) -> dict:
        """
        Вывод в API
        """
        dict_self = copy(self.__dict__)

        ignore_fields = ['log_level', 'exc_info', "peer_id"]
        for ignore_field in ignore_fields:
            del dict_self[ignore_field]
        dict_self["attachments"] = [x.to_api() for x in dict_self["attachments"]]

        return dict_self

    def set_telegram_html(self):
        if not self.text:
            return
        p = re.compile(self.URLS_REGEXP)  # Ссылки
        if p.search(self.text):
            self.parse_mode = TelegramParseMode.HTML
        else:
            for tag in self.TG_TAGS:
                p = re.compile(rf"<{tag}.*>[\s\S]*</{tag}>")
                if p.search(self.text):
                    self.parse_mode = TelegramParseMode.HTML
                    break

        if self.kwargs.get('parse_mode'):
            self.wrap_links()

    # def escape_markdown_v2(self):
    #     """Экранирует строку под parse_mode=MarkdownV2."""
    #     SPECIAL_CHARS = set('_*[]()~`>#+-=|{}.!')
    #
    #     escaped = []
    #     for ch in self.text:
    #         if ch == '\\':
    #             escaped.append('\\\\')
    #         elif ch in SPECIAL_CHARS:
    #             escaped.append(f'\\{ch}')
    #         else:
    #             escaped.append(ch)
    #     self.text = ''.join(escaped)

    def wrap_links(self):
        # Врапим ссылки без явного их врапа если у нас уже html
        url_poss = re.finditer(self.URLS_REGEXP, self.text)  # Ссылки не в скобках
        url_poss = reversed(list(url_poss))  # Заменяем всё в строке с конца, чтобы были корректные позиции
        for url_pos in url_poss:
            start_pos = url_pos.start()
            end_pos = url_pos.end()

            url = self.text[start_pos:end_pos]

            # Если ссылка уже враплена, то продолжаем просто дальше
            left_part = None
            right_part = None
            if start_pos >= 9:
                left_part = self.text[start_pos - 9:start_pos]
            if len(self.text) > end_pos:
                right_part = self.text[end_pos:end_pos + 2]
            if left_part == '<a href="' and right_part == '">':
                continue

            if len(self.attachments) < 2:
                from apps.bot.core.bot.telegram.tg_bot import TgBot
                self.text = self.text[:start_pos] + TgBot.get_formatted_url(url, url) + self.text[end_pos:]

    def __str__(self):
        return self.text if self.text else ""

    def get_tg_params(self) -> dict:
        params: dict = {
            'chat_id': self.peer_id,
            **self.kwargs
        }
        if self.text:
            if self.attachments:
                params['caption'] = self.text
            else:
                params['text'] = self.text

        if self.parse_mode:
            params['parse_mode'] = self.parse_mode

        if self.keyboard:
            params['reply_markup'] = self.keyboard
        if self.reply_to:
            params['reply_to_message_id'] = self.reply_to
        if self.disable_web_page_preview:
            params['disable_web_page_preview'] = True
        if self.message_thread_id:
            params['message_thread_id'] = self.message_thread_id
        if self.entities:
            params['entities'] = json.dumps(self.entities)

        if self.message_id:
            params['message_id'] = self.message_id
        return params


class ResponseMessage:
    def __init__(self, messages=None, send: bool = True, send_delay: int = 0):
        self.send = send
        self.send_delay = send_delay

        if messages is None:
            messages = []
        self.messages: list[ResponseMessageItem] = messages if isinstance(messages, list) else [messages]

    def to_log(self) -> dict:
        """
        Вывод в логи
        """
        dict_self = copy(self.__dict__)
        dict_self["messages"] = [x.to_log() for x in dict_self["messages"]]
        return dict_self

    def to_api(self) -> dict:
        """
        Вывод в API
        """
        dict_self = copy(self.__dict__)
        dict_self["messages"] = [x.to_api() for x in dict_self["messages"]]

        return dict_self

    def __bool__(self):
        return len(self.messages) > 0

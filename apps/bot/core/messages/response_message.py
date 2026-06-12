import re
from collections.abc import Sequence
from copy import copy

from apps.bot.core.messages.attachments.attachment import Attachment
from apps.bot.core.messages.telegram.parse_mode import TelegramParseMode


class ResponseMessageItem:
    TG_TAGS = ["pre", "code", "tg-spoiler", "i", "b", "u", "a", "s", "blockquote"]

    URLS_REGEXP = r"(http|ftp|https|tg)(:\/\/)([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])"

    def __init__(
        self,
        text: str | None = None,
        attachments: Attachment | Sequence[Attachment] | None = None,
        reply_to: int | None = None,
        keyboard: dict | None = None,
        message_id: int | None = None,
        message_thread_id: int | None = None,
        peer_id: int | None = None,
        log_level: str = "debug",
        exc_info=None,
        send: bool = True,
        spoiler: bool = False,
        parse_mode: TelegramParseMode | None = None,
        rich_markdown: str | None = None,
    ):
        self._raw_text = text
        self.text = text
        if attachments is None:
            self.attachments: list[Attachment] = []
        elif isinstance(attachments, Sequence):
            self.attachments = list(attachments)
        else:
            self.attachments = [attachments]
        self.reply_to = reply_to
        self.keyboard = keyboard
        self.message_id = message_id
        self.message_thread_id = message_thread_id
        self.peer_id = peer_id

        self.log_level = log_level
        self.exc_info = exc_info

        self.send = send
        self.spoiler = spoiler
        self.parse_mode = parse_mode
        self.rich_markdown = rich_markdown

    @property
    def has_rich_message(self) -> bool:
        return bool(self.rich_markdown)

    def set_rich_markdown(self, text: str | None = None):
        text = self.text if text is None else text
        if not text or self.rich_markdown:
            return

        self.rich_markdown = text

    def to_log(self) -> dict:
        """
        Вывод в логи
        """
        dict_self = copy(self.__dict__)
        ignore_fields = ["log_level", "exc_info"]
        for ignore_field in ignore_fields:
            del dict_self[ignore_field]

        dict_self["attachments"] = [x.to_log() for x in dict_self["attachments"]]
        return dict_self

    # TODO: unused
    def set_telegram_markdown_v2(self):
        if not self.text:
            return
        if self.parse_mode:
            return

        import telegramify_markdown

        self.text = telegramify_markdown.markdownify(
            self.text,
            max_line_length=None,
            # If you want to change the max line length for links, images, set it to the desired value.
            normalize_whitespace=False,
        )
        self.parse_mode = TelegramParseMode.MARKDOWN_V2

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

    def wrap_links(self):
        # Врапим ссылки без явного их врапа если у нас уже html
        if self.text is None:
            return

        text = self.text
        url_poss = re.finditer(self.URLS_REGEXP, text)  # Ссылки не в скобках
        url_poss = reversed(list(url_poss))  # Заменяем всё в строке с конца, чтобы были корректные позиции
        for url_pos in url_poss:
            start_pos = url_pos.start()
            end_pos = url_pos.end()

            url = text[start_pos:end_pos]

            # Если ссылка уже враплена, то продолжаем просто дальше
            left_part = None
            right_part = None
            if start_pos >= 9:
                left_part = text[start_pos - 9 : start_pos]
            if len(text) > end_pos:
                right_part = text[end_pos : end_pos + 2]
            if left_part == '<a href="' and right_part == '">':
                continue

            if len(self.attachments) < 2:
                from apps.bot.core.bot.telegram.tg_bot import TgBot

                text = text[:start_pos] + TgBot.get_formatted_url(url, url) + text[end_pos:]

        self.text = text

    def __str__(self):
        return self.text if self.text else ""

    def get_tg_params(self) -> dict:
        params: dict = {"chat_id": self.peer_id}
        if self.text:
            if self.attachments:
                params["caption"] = self.text
            else:
                params["text"] = self.text

        if self.parse_mode:
            params["parse_mode"] = self.parse_mode
        if self.rich_markdown:
            params["rich_markdown"] = self.rich_markdown

        if self.keyboard:
            params["reply_markup"] = self.keyboard
        if self.reply_to is not None:
            params["reply_to_message_id"] = self.reply_to
        if self.message_thread_id is not None:
            params["message_thread_id"] = self.message_thread_id

        if self.message_id is not None:
            params["message_id"] = self.message_id
        return params


class ResponseMessage:
    def __init__(
        self,
        messages: ResponseMessageItem | list[ResponseMessageItem] | None = None,
        send: bool = True,
        send_delay: int = 0,
    ):
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

    def __bool__(self):
        return len(self.messages) > 0

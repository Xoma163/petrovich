import re
from copy import copy

from apps.bot.utils.utils import get_tg_formatted_url


class ResponseMessage:
    def __init__(self, msgs, peer_id):
        self.messages = []

        if isinstance(msgs, list):
            for item in msgs:
                rmi = ResponseMessageItem(item, peer_id)
                self.messages.append(rmi)
        else:
            self.messages = [ResponseMessageItem(msgs, peer_id)] if msgs else []

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

    def __str__(self):
        return "\n".join([str(message) if message else "" for message in self.messages])


class ResponseMessageItem:
    def __init__(self, msg, peer_id):
        if isinstance(msg, str) or isinstance(msg, int) or isinstance(msg, float):
            msg = {'text': str(msg)}

        msg_copy = copy(msg)

        self.peer_id = peer_id
        self.text = str(msg_copy.pop("text", ""))
        self.attachments = msg_copy.pop("attachments", [])
        if not isinstance(self.attachments, list):
            self.attachments = [self.attachments]
        self.keyboard = msg_copy.pop("keyboard", {})
        self.kwargs = msg_copy

    def to_log(self) -> dict:
        """
        Вывод в логи
        """
        dict_self = copy(self.__dict__)
        dict_self["attachments"] = [x.to_log() for x in dict_self["attachments"] if isinstance(x, dict)]
        return dict_self

    def to_api(self) -> dict:
        """
        Вывод в API
        """
        dict_self = copy(self.__dict__)
        dict_self["attachments"] = [x.to_api() for x in dict_self["attachments"]]
        del dict_self["peer_id"]

        return dict_self

    def set_telegram_html(self):
        urls_regexp = r"(http|ftp|https|tg)(:\/\/)([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])"
        if self.text:
            p = re.compile(urls_regexp)  # Ссылки
            if p.search(self.text):
                self.kwargs = {'parse_mode': "html"}

            p = re.compile("<pre>[\s\S]*</pre>")  # tg formatting
            if p.search(self.text):
                self.kwargs = {'parse_mode': "html"}

            p = re.compile("<code>[\s\S]*</code>")  # tg formatting
            if p.search(self.text):
                self.kwargs = {'parse_mode': "html"}

            if self.kwargs.get('parse_mode'):
                # Врапим ссылки без явного их врапа если у нас уже html
                url_poss = re.finditer(urls_regexp, self.text)  # Ссылки не в скобках
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

                    self.text = self.text[:start_pos] + get_tg_formatted_url(url, url) + self.text[end_pos:]

                    # self.text = self.text.replace(url, get_tg_formatted_url(url, url))

    def __str__(self):
        return self.text if self.text else ""

import io
import json
import logging
import textwrap

from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import draw_text_on_image
from petrovich.settings import DEBUG_FILE


class Logs(Command):
    DEFAULT_LEVEL = logging.DEBUG
    DEFAULT_LEVEL_NAME = "DEBUG"
    DEFAULT_COUNT = 3
    MAX_LOGS_COUNT = 50

    name = "логи"
    names = ["лог"]
    name_tg = 'logs'

    help_text = "логи бота"
    help_texts = [f"[уровень логов = {DEFAULT_LEVEL}] [кол-во записей = {DEFAULT_COUNT}] - логи."]
    help_texts_extra = f"Макс {MAX_LOGS_COUNT} записей. Возможные уровни логов: DEBUG/INFO/WARNING/ERROR/CRITICAL"

    access = Role.MODERATOR

    def start(self) -> ResponseMessage:
        count = self.DEFAULT_COUNT

        level = self.DEFAULT_LEVEL
        level_name = self.DEFAULT_LEVEL_NAME
        if self.event.message.args:
            level = logging._nameToLevel.get(self.event.message.args[0].upper(), logging._nameToLevel[level_name])

            self.int_args = [-1]
            try:
                self.parse_int()
                count = self.event.message.args[-1]
                count = min(count, self.MAX_LOGS_COUNT)
            except PWarning:
                pass

        filter_levels = [logging._levelToName[x] for x in logging._levelToName if x >= level]
        separator = "-" * 150

        logs_list = self.get_bot_logs(count, filter_levels)
        for b in range(0, len(logs_list)):
            logs_list.insert(b * 2 + 1, separator)
        logs_txt = "\n".join(logs_list)
        img = draw_text_on_image(logs_txt)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')

        attachment = self.bot.get_document_attachment(img_byte_arr, peer_id=self.event.peer_id,
                                                      filename='petrovich_logs.png')
        return ResponseMessage(ResponseMessageItem(attachments=attachment))

    def transform_logs_by_values(self, items):
        if isinstance(items, dict):
            keys_to_del = []
            for key in items:
                item = items[key]
                if not item:
                    keys_to_del.append(key)
                    continue
                if isinstance(item, dict):
                    self.transform_logs_by_values(item)
                    if not item:
                        keys_to_del.append(key)
                elif isinstance(item, list):
                    for _item in item:
                        self.transform_logs_by_values(item)
                        if not item:
                            keys_to_del.append(key)
                else:
                    if item in ["null", "*****"]:
                        keys_to_del.append(key)
                    elif isinstance(item, str) and "\n" in item:
                        items[key] = item.split('\n')
            for key in keys_to_del:
                del items[key]
        elif isinstance(items, list):
            for item in items:
                self.transform_logs_by_values(item)

    def wrap_long_texts(self, items, wrap_val=150) -> object:
        if isinstance(items, dict):
            for key in items:
                item = items[key]
                if isinstance(item, dict):
                    items[key] = self.wrap_long_texts(item)
                elif isinstance(item, list):
                    for i, _item in enumerate(item):
                        items[key][i] = self.wrap_long_texts(_item)
                elif isinstance(item, str) and len(item) > wrap_val:
                    items[key] = textwrap.fill(item, wrap_val).replace('\\n', '\n')
            return items
        elif isinstance(items, list):
            for i, item in enumerate(items):
                items[i] = self.wrap_long_texts(item)
            return items
        elif isinstance(items, str):
            if len(items) > wrap_val:
                return textwrap.fill(items, wrap_val).replace('\\n', '\n')
            return items
        else:
            return items

    def get_bot_logs(self, count, filter_level=None):
        file_rows = self.read_file(DEBUG_FILE)
        res = []
        for i in range(len(file_rows) - 2, -1, -1):
            item_json = json.loads(file_rows[i])
            if filter_level and item_json['levelname'] not in filter_level:
                continue
            self.transform_logs_by_values(item_json)
            self.wrap_long_texts(item_json)
            item_str = json.dumps(item_json, indent=2, ensure_ascii=False).replace('\\n', '\n')
            res.append(item_str)

            if len(res) >= count:
                break
        res = list(reversed(res))
        return res

    def get_count(self, default, max_count):
        if self.event.message.args:
            try:
                count = int(self.event.message.args[-1])
                return min(count, max_count)
            except ValueError:
                pass
        return default

    @staticmethod
    def read_file(path):
        with open(path, 'r') as file:
            lines = file.readlines()
        return lines

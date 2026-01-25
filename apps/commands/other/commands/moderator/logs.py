import json
import logging
import textwrap

from apps.bot.consts import RoleEnum
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.commands.command import Command
from apps.commands.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.shared.exceptions import PWarning
from apps.shared.utils.utils import draw_text_on_image, convert_pil_image_to_bytes
from petrovich.settings import DEBUG_FILE


class Logs(Command):
    DEFAULT_LEVEL = logging.DEBUG
    DEFAULT_LEVEL_NAME = "DEBUG"
    DEFAULT_COUNT = 2
    MAX_LOGS_COUNT = 15

    name = "логи"
    names = ["лог"]
    access = RoleEnum.MODERATOR

    help_text = HelpText(
        commands_text="логи бота",
        help_texts=[
            HelpTextItem(access, [
                HelpTextArgument(f"[уровень логов = {DEFAULT_LEVEL_NAME}] [кол-во записей = {DEFAULT_COUNT}]", "логи")
            ])
        ],
        extra_text=(
            f"Макс {MAX_LOGS_COUNT} записей. Возможные уровни логов: DEBUG/INFO/WARNING/ERROR/CRITICAL"
        )
    )

    def start(self) -> ResponseMessage:
        count = self.DEFAULT_COUNT
        level = self.DEFAULT_LEVEL
        if self.event.message.args:
            level = logging.getLevelNamesMapping().get(self.event.message.args[0].upper(), level)

            self.int_args = [-1]
            try:
                self.parse_int()
                count = self.event.message.args[-1]
                count = min(count, self.MAX_LOGS_COUNT)
            except PWarning:
                pass

        filter_levels = [x[0] for x in logging.getLevelNamesMapping().items() if x[1] >= level]
        logs_list = self.get_bot_logs(count, filter_levels)

        separator = "-" * 150
        for i in range(0, len(logs_list)):
            logs_list.insert(i * 2 + 1, separator)
        logs_txt = "\n".join(logs_list)
        img = draw_text_on_image(logs_txt)
        _bytes = convert_pil_image_to_bytes(img)

        document = self.bot.get_document_attachment(
            _bytes=_bytes,
            thumbnail_bytes=_bytes,
            peer_id=self.event.peer_id,
            filename='petrovich_logs.png',
        )
        # document.set_thumbnail(document.content)
        return ResponseMessage(ResponseMessageItem(attachments=[document]))

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

    def wrap_long_texts(self, items, wrap_val=150):
        if isinstance(items, dict):
            for key, item in items.items():
                items[key] = self.wrap_long_texts(item, wrap_val)
            return items
        elif isinstance(items, list):
            return [self.wrap_long_texts(item, wrap_val) for item in items]
        elif isinstance(items, str) and len(items) > wrap_val:
            return textwrap.fill(items, wrap_val).replace('\\n', '\n')
        return items

    def get_bot_logs(self, count, filter_level=None):
        file_rows = self.read_file(DEBUG_FILE)
        res = []
        found_logs = 0
        last_message_id = 0
        for i in range(len(file_rows) - 1, -1, -1):
            item_json = json.loads(file_rows[i])
            if not item_json.get('log_filter'):
                continue

            log_filter = item_json.pop('log_filter')

            item_json = self.filter_row(item_json, log_filter, filter_level)
            if not item_json:
                continue

            if log_filter['message_id'] != last_message_id:
                found_logs += 1
                res.append("")

            last_message_id = log_filter['message_id']

            if found_logs > count:
                break

            self.transform_logs_by_values(item_json)
            self.wrap_long_texts(item_json)
            item_str = json.dumps(item_json, indent=2, ensure_ascii=False).replace('\\n', '\n')
            res.append(item_str)
        return list(reversed(res))

    def filter_row(self, item_json, log_filter, filter_level):
        # filter by chat/user
        if self.event.chat:
            if log_filter['chat_id'] != self.event.chat.chat_id:
                return None
        else:
            if log_filter['chat_id'] is not None:
                return None
            if log_filter['user_id'] != self.event.user.user_id:
                return None

        # filter by level
        if filter_level and item_json['levelname'] not in filter_level:
            return None

        # filter by content
        if 'action' in item_json and item_json['action'] == 'sendChatAction':
            return None

        # drop trash
        if 'event' in item_json and 'raw' in item_json['event']:
            item_json['event'].pop('raw')

        return item_json

    @staticmethod
    def read_file(path):
        with open(path, 'r') as file:
            lines = file.readlines()
        return lines

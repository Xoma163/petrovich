import io
import json
import logging

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import draw_text_on_image
from petrovich.settings import DEBUG_FILE


class Logs(Command):
    name = "логи"
    names = ["лог"]
    name_tg = 'logs'

    help_text = "логи бота"
    help_texts = [
        "[уровень логов = DEBUG] [кол-во записей=10] - логи. Макс 30 записей. Возможные уровни логов: DEBUG/INFO/WARNING/ERROR/CRITICAL"
    ]

    access = Role.MODERATOR
    platforms = [Platform.VK, Platform.TG]

    MAX_LOGS_COUNT = 50

    def start(self):
        count = 10

        level = logging.DEBUG
        level_name = "DEBUG"
        if self.event.message.args:
            level = logging._nameToLevel.get(self.event.message.args[0].upper(), logging._nameToLevel[level_name])

            self.int_args = [-1]
            try:
                self.parse_int()
                count = self.event.message.args[-1]
                count = min(count, 30)
            except PWarning:
                pass

        filter_levels = [logging._levelToName[x] for x in logging._levelToName if x >= level]
        filter_chat = self.event.peer_id if self.event.chat else None

        logs_txt = self.get_bot_logs(count, filter_chat, filter_levels)
        img = draw_text_on_image(logs_txt)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return {'attachments': self.bot.upload_document(img_byte_arr, peer_id=self.event.peer_id, filename='logs.png')}

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

    def get_bot_logs(self, count, filter_chat=None, filter_level=None):
        file_rows = self.read_file(DEBUG_FILE)
        separator = "-" * 150
        res2 = []
        for i in range(len(file_rows) - 1, -1, -1):
            item_json = json.loads(file_rows[i])
            if filter_chat and 'event' in item_json and str(item_json['event']['peer_id']) != self.event.chat.chat_id:
                continue
            if filter_level and item_json['levelname'] not in filter_level:
                continue
            self.transform_logs_by_values(item_json)
            item_str = json.dumps(item_json, indent=2, ensure_ascii=False)
            res2.append(separator)
            res2.append(item_str)

            if len(res2) > count:
                break
        res2.append(separator)
        text = "\n".join(res2)
        return text

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
            lines = file.readlines()  # [-rows_count:]
        return lines

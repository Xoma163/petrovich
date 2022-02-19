import io
import json

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.utils.utils import draw_text_on_image
from petrovich.settings import DEBUG_FILE


class Logs(Command):
    name = "логи"
    names = ["лог"]
    name_tg = 'logs'

    help_text = "логи бота"
    help_texts = [
        "[кол-во строк=10] - логи. Макс 50 строк."
    ]

    access = Role.MODERATOR
    platforms = [Platform.VK, Platform.TG]

    MAX_LOGS_COUNT = 50

    def start(self):
        logs_txt = self.get_bot_logs()
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

    def get_bot_logs(self):
        count = self.get_count(10, self.MAX_LOGS_COUNT)
        res = self.read_file(DEBUG_FILE, count)
        res2 = []
        separator = "-" * 150
        for item in res:
            item_json = json.loads(item)
            self.transform_logs_by_values(item_json)
            item_str = json.dumps(item_json, indent=2, ensure_ascii=False)
            res2.append(separator)
            res2.append(item_str)
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
    def read_file(path, rows_count):
        with open(path, 'r') as file:
            lines = file.readlines()[-rows_count:]
        return lines

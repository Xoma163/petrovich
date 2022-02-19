import requests

from apps.bot.classes.consts.Exceptions import PWarning, PError
from petrovich.settings import env


class Openhab3API:
    URL = env.str("OPENHAB3_API_URL")
    TOKEN = env.str("OPENHAB3_API_TOKEN")
    HEADERS = {
        "Accept": "application/json",
        "Authorization": f"Bearer {TOKEN}"
    }

    def get_items(self, room=None):
        params = {
            'recursive': True
        }
        items = requests.get(f"{self.URL}/items", params, headers=self.HEADERS).json()
        if 'error' in items:
            raise PWarning("Ошибка")
        if room:
            items = list(filter(lambda x: room in x['groupNames'], items))
        return self._strip_items_fields(items)

    @staticmethod
    def _strip_items_fields(items):
        parsed_items = []
        for item in items:
            parsed_item = {
                'name': item['name'],
                'label': item['label'],
                'type': item['type'],
                'category': item['category'],
                'sub_items': []
            }
            sub_items = item.get('members', [])
            for sub_item in sub_items:
                parsed_sub_item = {
                    'name': sub_item['name'],
                    'label': sub_item['label'],
                    'type': sub_item['type'],
                    'state': sub_item['state'],
                }
                if sub_item.get('stateDescription'):
                    parsed_sub_item['uom'] = sub_item['stateDescription']['pattern'].replace("%s", '').replace("%%",
                                                                                                               "%")
                parsed_item['sub_items'].append(parsed_sub_item)
            parsed_items.append(parsed_item)
        return parsed_items

    def set_item_state(self, item_name, state):
        items = self.get_items()
        item = self.find_item_by_label(items, item_name)

        state = "ON" if state else "OFF"
        headers = {
            "Content-Type": "text/plain"
        }
        headers.update(self.HEADERS)
        res = requests.post(f"{self.URL}/items/{item['name']}/", data=state, headers=headers)
        if res.status_code != 200:
            raise PError("Ошибка")

    @staticmethod
    def find_item_by_label(items, label):
        label_lower = label.lower()
        for item in items:
            for sub_item in item['sub_items']:
                if sub_item['label'].lower() == label_lower:
                    return sub_item
        raise PWarning(f"Не нашёл устройства с именем {label}")

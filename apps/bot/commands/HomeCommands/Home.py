from apps.bot.APIs.Openhab3API import Openhab3API
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role, ON_OFF_TRANSLATOR, TRUE_FALSE_TRANSLATOR
from apps.bot.classes.consts.Exceptions import PWarning


class Home(Command):
    name = "дом"
    help_text = "значение датчиков и состояние устройств в доме"
    help_texts = [
        "- значение датчиков и состояние устройств в доме",
        "(комната) - значение датчиков и состояние устройств в комнате",
        "(устройство) (вкл/выкл) - управление устройством в доме"
    ]
    access = Role.HOME

    ROOMS = {
        'LivingRoom': {
            'name': "Гостиная",
            'items_names': [
                'Humidifier',
                'RGB_strip',
                'Fan',
                'Meteostation1',
                'heater_in_legs',
                "OctoPrint_server"
            ]
        },
        'Bedroom': {
            'name': "Спальня",
            'items_names': [
                "Heater",
                "Meteostation2"
            ]
        },
        'Bathroom': {
            'name': "Ванная",
            'items_names': [
                "meteostation_3"
            ]
        }
    }

    def start(self):
        if not self.event.message.args:
            return self.get_home_items()
        else:
            try:
                room = self.get_room_by_name(self.event.message.args[0])
                return self.get_room_items(room)
            except PWarning:
                self.args = 2
                self.check_args()

            return self.set_item_state(self.event.message.args[:-1], self.event.message.args[-1])

    def get_home_items(self):
        msgs = []
        oh3_api = Openhab3API()
        items = oh3_api.get_items()
        for room in self.ROOMS:
            data = self.ROOMS[room]
            room_name = data['name']
            room_items = self.filter_room_items(items, room)
            room_msg = f"{room_name}:\n{self.prepare_items_to_msg(room_items)}"
            msgs.append(room_msg)
        return f"{'-' * 40}\n".join(msgs)

    def get_room_items(self, room):
        oh3 = Openhab3API()
        items = oh3.get_items(room)
        items = self.filter_room_items(items, room)
        return self.prepare_items_to_msg(items)

    def filter_room_items(self, items, room):
        return list(filter(lambda x: x['name'] in self.ROOMS[room]['items_names'], items))

    @staticmethod
    def set_item_state(item_name, state):
        state_translated = ON_OFF_TRANSLATOR.get(state)
        if state_translated is None:
            raise PWarning(f"Я не знаю состояния {state}")
        item_name = " ".join(item_name)
        oh3 = Openhab3API()
        oh3.set_item_state(item_name, state_translated)
        return f"Поменял состояние на {state}"

    def get_room_by_name(self, arg):
        for k in self.ROOMS:
            data = self.ROOMS[k]
            if arg == data['name'].lower():
                return k
        raise PWarning(f"Не нашёл комнаты {arg}")

    @staticmethod
    def prepare_items_to_msg(items):
        msgs = []
        for item in items:
            item_msg = f"{item['label']}:\n"
            for sub_item in item['sub_items']:
                if item['category'] == 'sensors':
                    if sub_item.get("uom"):
                        item_msg += f'{sub_item["label"]} - {sub_item["state"]}{sub_item["uom"]}\n'
                elif sub_item['type'] == 'Switch':
                    state = TRUE_FALSE_TRANSLATOR[ON_OFF_TRANSLATOR[sub_item['state'].lower()]]
                    item_msg += f'{sub_item["label"]} - {state}\n'
            msgs.append(item_msg)
        return "\n".join(msgs)

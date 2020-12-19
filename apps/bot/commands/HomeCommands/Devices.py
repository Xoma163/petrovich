from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand
from .Sensors import get_data_for_items, get_items, get_room_and_item_by_args

DEVICES = [
    # {'name': "Обогреватель", 'table': "Item0003", 'topic': 'cmnd/tasmota_5C048E/POWER', 'type': bool},
    {'name': "Спальня", 'items': [
        # {'name': "Лампы", 'table': "Item0001", 'topic': 'cmnd/tasmota_50E93E/POWER', 'type': bool},

    ]},
    {'name': "Гостинная", 'items': [
        {'name': "Лента", 'table': "Item0020", 'type': bool},
        # {'name': "Обогреватель", 'table': "Item0002", 'topic': 'cmnd/tasmota_152F6A/POWER', 'type': bool},

    ]},
    {'name': "Кухня", 'items': [
        # {'name': "Обогреватель", 'table': "Item0005", 'topic': 'cmnd/tasmota_C1E41A/POWER', 'type': bool},
    ]}
]


class Sensors(CommonCommand):
    def __init__(self):
        names = ["устройства"]
        help_text = "Устройства - значение датчиков и состояние устройств в доме"
        detail_help_text = "Устройства [комната = все] [датчик = все] - устройства из дома"
        super().__init__(names, help_text, detail_help_text, access=Role.HOME)

    def start(self):
        if self.event.args:
            room_name, item_name = get_room_and_item_by_args(self.event.args)
            items = get_items(DEVICES, room_name, item_name)
        else:
            items = DEVICES
        sensors_data = get_data_for_items(items)
        return sensors_data

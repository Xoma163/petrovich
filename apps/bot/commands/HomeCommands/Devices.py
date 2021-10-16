from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from .Sensors import get_data_for_items, get_items, get_room_and_item_by_args

DEVICES = [
    # {'name': "Обогреватель", 'table': "Item0003", 'topic': 'cmnd/tasmota_5C048E/POWER', 'type': bool},
    {'name': "Спальня", 'items': [
        # {'name': "Лампы", 'table': "Item0001", 'topic': 'cmnd/tasmota_50E93E/POWER', 'type': bool},

    ]},
    {'name': "Гостиная", 'items': [
        {'name': "Лента", 'table': "Item0020", 'type': bool},
        # {'name': "Обогреватель", 'table': "Item0002", 'topic': 'cmnd/tasmota_152F6A/POWER', 'type': bool},

    ]},
    {'name': "Кухня", 'items': [
        # {'name': "Обогреватель", 'table': "Item0005", 'topic': 'cmnd/tasmota_C1E41A/POWER', 'type': bool},
    ]}
]


class Sensors(Command):
    name = "устройства"
    help_text = "значение датчиков и состояние устройств в доме"
    help_texts = [
        "- значение датчиков и состояние устройств в доме",
        "[комната = все] [датчик = все] - устройства из дома",
        "(комната) - устройства в комнате",
        "(название датчика) - устройства по фильтру"
    ]
    access = Role.HOME

    def start(self):
        if self.event.message.args:
            room_name, item_name = get_room_and_item_by_args(self.event.message.args)
            items = get_items(DEVICES, room_name, item_name)
        else:
            items = DEVICES
        sensors_data = get_data_for_items(items)
        return sensors_data

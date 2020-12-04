from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand
from .Sensors import get_item, get_data_for_items

DEVICES = [
    # {'name': "Лампы", 'table': "Item0001", 'topic': 'cmnd/tasmota_50E93E/POWER', 'type': bool},
    # {'name': "Обогреватель", 'table': "Item0003", 'topic': 'cmnd/tasmota_5C048E/POWER', 'type': bool},
    # {'name': "Обогреватель в ногах", 'table': "Item0002", 'topic': 'cmnd/tasmota_152F6A/POWER', 'type': bool},
    # {'name': "Обогреватель на кухне", 'table': "Item0005", 'topic': 'cmnd/tasmota_C1E41A/POWER', 'type': bool},
    # {'name': "Лента", 'table': "Item0020", 'type': bool},
]


class Sensors(CommonCommand):
    def __init__(self):
        names = ["устройства"]
        help_text = "Устройства - значение датчиков и состояние устройств в доме"
        detail_help_text = "Устройства [название датчика = все] - датчики из дома"
        super().__init__(names, help_text, detail_help_text, access=Role.HOME)

    def start(self):
        if self.event.args:
            item = get_item(self.event.original_args.lower(), DEVICES)
            items = [item]
        else:
            items = DEVICES
        sensors_list_data = get_data_for_items(items)
        result = "\n".join(sensors_list_data)
        return result

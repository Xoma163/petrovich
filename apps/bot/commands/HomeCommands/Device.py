import paho.mqtt.client as mqtt

from apps.bot.classes.Consts import Role, ON_OFF_TRANSLATOR
from apps.bot.classes.common.CommonCommand import CommonCommand
from petrovich.settings import env
from .Devices import DEVICES
from .Sensors import get_item

TRUE_FALSE_TRANSLATOR_ON_OFF = {
    True: 'ON',
    False: 'OFF'
}


class Sensors(CommonCommand):
    def __init__(self):
        names = ["устройство"]
        help_text = "Устройство - включает или выключает устройства в доме"
        detail_help_text = "Устройство (название устройства) (вкл/выкл) - включает или выключает устройство в доме"
        super().__init__(names, help_text, detail_help_text, access=Role.HOME, args=2)

    @staticmethod
    def set_device_state(device, state):
        if 'topic' not in device:
            raise RuntimeWarning("Этим устройством невозможно управлять")
        client = mqtt.Client("petrovich")
        client.username_pw_set(username=env.str('MQTT_USER'), password=env.str('MQTT_PASSWORD'))
        client.connect(env.str('MQTT_SERVER'))
        client.publish(device['topic'], state)
        client.disconnect()

    def start(self):
        state = ON_OFF_TRANSLATOR.get(self.event.args[-1], None)
        if state is None:
            raise RuntimeWarning("Не знаю такого состояния")
        item_name = " ".join(self.event.args[:-1])
        item = get_item(item_name, DEVICES)
        self.set_device_state(item, TRUE_FALSE_TRANSLATOR_ON_OFF[state])
        if state:
            return f"Включил {item['name'].lower()}"
        else:
            return f"Выключил {item['name'].lower()}"

import paho.mqtt.client as mqtt

from apps.bot.classes.Consts import Role, ON_OFF_TRANSLATOR
from apps.bot.classes.common.CommonCommand import CommonCommand
from petrovich.settings import env
from .Devices import DEVICES
from .Sensors import get_items, get_room_and_item_by_args
from ...classes.Exceptions import PWarning

TRUE_FALSE_TRANSLATOR_ON_OFF = {
    True: 'ON',
    False: 'OFF'
}


class Sensors(CommonCommand):
    name = "устройство"
    help_text = "включает или выключает устройства в доме"
    help_texts = ["[комната = все] (устройство) (вкл/выкл) - управляет устройством в доме"]
    access = Role.HOME
    args = 2

    @staticmethod
    def set_device_state(device, state):
        if 'topic' not in device:
            raise PWarning("Этим устройством невозможно управлять")
        client = mqtt.Client("petrovich")
        client.username_pw_set(username=env.str('MQTT_USER'), password=env.str('MQTT_PASSWORD'))
        client.connect(env.str('MQTT_SERVER'))
        client.publish(device['topic'], state)
        client.disconnect()

    def start(self):
        state = ON_OFF_TRANSLATOR.get(self.event.message.args[-1], None)
        if state is None:
            raise PWarning("Не знаю такого состояния")

        room_name, item_name = get_room_and_item_by_args(self.event.message.args[:-1])
        items = get_items(DEVICES, room_name, item_name)
        if len(items) > 1:
            raise PWarning("Под поиск подходит 2 и более устройств")
        item = items[0]['items']
        if len(item) > 1:
            raise PWarning("Под поиск подходит 2 и более устройств")
        item = item[0]
        self.set_device_state(item, TRUE_FALSE_TRANSLATOR_ON_OFF[state])
        if state:
            return f"Включил {item['name'].lower()}"
        else:
            return f"Выключил {item['name'].lower()}"

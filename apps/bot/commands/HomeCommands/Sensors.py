import psycopg2

from apps.bot.classes.Consts import Role, TRUE_FALSE_TRANSLATOR, ON_OFF_TRANSLATOR
from apps.bot.classes.common.CommonCommand import CommonCommand
from petrovich.settings import env

TRUE_FALSE_TRANSLATOR_ON_OFF = {
    True: 'ON',
    False: 'OFF'
}

SENSORS = [
    {'name': "Температура", 'table': "Item0021", 'unit': '°C', 'accuracy': 1, 'type': float},
    {'name': "Давление", 'table': "Item0009", 'unit': "мм. рт.ст.", 'type': int},
    {'name': "Влажность", 'table': "Item0015", 'unit': '%', 'type': int},
    {'name': "Углекислый газ", 'table': "Item0008", 'unit': 'ppm', 'type': int},
]


class Sensors(CommonCommand):
    def __init__(self):
        names = ["датчики"]
        help_text = "Датчики - значение датчиков и состояние устройств в доме"
        detail_help_text = "Датчики [название датчика = все] - датчики из дома"
        super().__init__(names, help_text, detail_help_text, access=Role.HOME)

    def start(self):
        if self.event.args:
            item = get_item(self.event.original_args.lower(), SENSORS)
            items = [item]
        else:
            items = SENSORS
        sensors_list_data = get_data_for_items(items)
        result = "\n".join(sensors_list_data)
        return result


def get_data_for_items(items):
    result = []
    for item in items:
        value = get_last_data(item)
        if item['type'] == int:
            value = int(value)
        elif item['type'] == float:
            value = round(value, item['accuracy'])
        elif item['type'] == bool:
            value = TRUE_FALSE_TRANSLATOR[ON_OFF_TRANSLATOR[value.lower()]]

        if 'unit' in item:
            result.append(f"{item['name']} - {value}{item['unit']}")
        else:
            result.append(f"{item['name']} - {value}")
    return result


def get_last_data(item):
    db = env.db('DATABASE_OPENHAB2_URL')
    conn = psycopg2.connect(
        f"dbname='{db['NAME']}' user='{db['USER']}' host='{db['HOST']}' password='{db['PASSWORD']}'")
    cur = conn.cursor()
    cur.execute(f"""SELECT value
                    FROM {item['table']} 
                    ORDER BY time DESC 
                    LIMIT 1 """)
    rows = cur.fetchall()
    conn.close()
    return rows[0][0]


def get_item(item_name, items):
    item_name = item_name.lower()
    for item in items:
        if item['name'].lower() == item_name:
            return item
    raise RuntimeWarning("Не нашёл такого устройства/датчика")

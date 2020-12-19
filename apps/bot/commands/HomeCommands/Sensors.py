import psycopg2

from apps.bot.classes.Consts import Role, TRUE_FALSE_TRANSLATOR, ON_OFF_TRANSLATOR
from apps.bot.classes.common.CommonCommand import CommonCommand
from petrovich.settings import env

TRUE_FALSE_TRANSLATOR_ON_OFF = {
    True: 'ON',
    False: 'OFF'
}

SENSORS = [
    {'name': "Спальня", 'items': [
        {'name': "Углекислый газ", 'table': "Item0008", 'unit': 'ppm', 'type': int},
        {'name': "Температура", 'table': "Item0021", 'unit': '°C', 'accuracy': 1, 'type': float},
        {'name': "Влажность", 'table': "Item0015", 'unit': '%', 'type': int},
        {'name': "Давление", 'table': "Item0009", 'unit': "мм. рт.ст.", 'type': int},
    ]},
    {'name': "Гостинная", 'items': [
        {'name': "Температура", 'table': "Item0022", 'unit': '°C', 'accuracy': 1, 'type': float},
        {'name': "Влажность", 'table': "Item0023", 'unit': '%', 'type': int},
        {'name': "Давление", 'table': "Item0024", 'unit': "мм. рт.ст.", 'type': int},
    ]},
    {'name': "Кухня", 'items': [
        {'name': "Температура", 'table': "Item0025", 'unit': '°C', 'accuracy': 1, 'type': float},
        {'name': "Влажность", 'table': "Item0026", 'unit': '%', 'type': int},
        {'name': "Давление", 'table': "Item0027", 'unit': "мм. рт.ст.", 'type': int},
    ]}
]


class Sensors(CommonCommand):
    def __init__(self):
        names = ["датчики"]
        help_text = "Датчики - значение датчиков и состояние устройств в доме"
        detail_help_text = "Датчики [комната = все] [датчик = все] - датчики из дома\n" \
                           "Датчики (комната) - датчики в комнате\n" \
                           "Датчики (название датчика) - датчики по фильтру\n"

        super().__init__(names, help_text, detail_help_text, access=Role.HOME)

    def start(self):
        if self.event.args:
            room_name, item_name = get_room_and_item_by_args(self.event.args)
            items = get_items(SENSORS, room_name, item_name)
        else:
            items = SENSORS
        sensors_data = get_data_for_items(items)
        return sensors_data


def get_room_and_item_by_args(args):
    rooms_name = [x['name'] for x in SENSORS]
    if args[0].capitalize() in rooms_name:
        room_name = args[0]
        item_name = None
        if len(args[0]) > 1:
            item_name = "".join(args[1:])
        return room_name, item_name
    else:
        return None, "".join(args)


def get_data_for_items(rooms):
    result = ""
    for room in rooms:
        result += f"{room['name']}:\n"
        for item in room['items']:
            value = get_last_data(item)
            if item['type'] == int:
                value = int(value)
            elif item['type'] == float:
                value = round(value, item['accuracy'])
            elif item['type'] == bool:
                value = TRUE_FALSE_TRANSLATOR[ON_OFF_TRANSLATOR[value.lower()]]
            elif item['type'] == str:
                value = str(value)

            if 'unit' in item:
                result += f"{item['name']} - {value}{item['unit']}\n"
            else:
                result += f"{item['name']} - {value}\n"
        result += f"\n"
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


def get_items(rooms, room_name=None, item_name=None):
    if room_name:
        rooms_name = [x['name'] for x in SENSORS]
        if room_name.capitalize() not in rooms_name:
            raise RuntimeWarning("Не нашел такой комнаты")
    result = []
    if item_name:
        for room in rooms:
            if room_name and room_name.lower() != room['name'].lower():
                continue
            result_room = {'name': room['name'], 'items': []}
            for item in room['items']:
                if item_name.lower() in item['name'].lower():
                    result_room['items'].append(item)
            if len(result_room['items']) > 0:
                result.append(result_room)
    if len(result) == 0:
        raise RuntimeWarning("Не нашёл такого устройства/датчика")
    return result

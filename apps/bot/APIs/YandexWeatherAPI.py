import json
import logging
from datetime import datetime

import requests

from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import remove_tz
from apps.service.models import Service, City
from petrovich.settings import env

DAY_TRANSLATOR = {
    'night': 'ночь',
    'morning': 'утро',
    'day': 'день',
    'evening': 'вечер',
}

WEATHER_TRANSLATOR = {
    'clear': 'Ясно ☀',
    'partly-cloudy': 'Малооблачно ⛅',
    'cloudy': 'Облачно с прояснениями 🌥',
    'overcast': 'Пасмурно ☁',
    'partly-cloudy-and-light-rain': 'Небольшой дождь 🌧',
    'partly-cloudy-and-rain': 'Дождь 🌧',
    'overcast-and-rain': 'Сильный дождь 🌧🌧',
    'overcast-thunderstorms-with-rain': 'Сильный дождь, гроза 🌩',
    'cloudy-and-light-rain': 'Небольшой дождь 🌧',
    'overcast-and-light-rain': 'Небольшой дождь 🌧',
    'cloudy-and-rain': 'Дождь 🌧',
    'overcast-and-wet-snow': 'Дождь со снегом 🌨',
    'partly-cloudy-and-light-snow': 'Небольшой снег 🌨',
    'partly-cloudy-and-snow': 'Снег 🌨',
    'overcast-and-snow': 'Снегопад 🌨',
    'cloudy-and-light-snow': 'Небольшой снег 🌨',
    'overcast-and-light-snow': 'Небольшой снег 🌨',
    'cloudy-and-snow': 'Снег 🌨'
}

WEATHER_WIND_DIRECTION_TRANSLATOR = {
    "nw": "северо-западный",
    "n": "северный",
    "ne": "северо-восточный",
    "e": "восточный",
    "se": "юго-восточный",
    "s": "южный",
    "sw": "юго-западный",
    "w": "западный",
    "c": "штиль",
}
logger = logging.getLogger('bot')


class YandexWeatherAPI:
    URL = "https://api.weather.yandex.ru/v1/informers"
    TOKEN = env.str("YANDEX_WEATHER_TOKEN")
    HEADERS = {
        'X-Yandex-API-Key': TOKEN
    }

    def send_weather_request(self, city: City):
        params = {
            'lat': city.lat,
            'lon': city.lon,
            'lang': 'ru_RU'
        }
        r = requests.get(self.URL, params, headers=self.HEADERS).json()
        logger.debug({"response": r})

        if 'status' in r:
            if r['status'] == 403:
                raise PWarning("На сегодня я исчерпал все запросы к Yandex Weather :(")

        return r

    def get_weather(self, city: City, use_cached=True):
        entity, created = Service.objects.get_or_create(name=f'weather_{city.name}')
        if use_cached and not created:
            delta_time = (datetime.utcnow() - remove_tz(entity.update_datetime))
            if delta_time.seconds < 3600 and delta_time.days == 0:
                weather_data = json.loads(entity.value)
                return weather_data

        weather_data = self.send_weather_request(city)
        entity.value = json.dumps(weather_data)
        entity.save()
        return weather_data

    def get_weather_str(self, city):
        data = self.get_weather(city)

        now = self.get_weather_part_str(data['fact'])

        forecasts = [self.get_weather_part_str(x) for x in data['forecast']['parts']]
        forecasts_str = "\n\n".join(forecasts)
        return f"Погода в г. {city.name} сейчас:\n" \
               f"{now}\n\n" \
               f"{forecasts_str}"

    @staticmethod
    def get_weather_part_str(data):
        res = [
            f"{WEATHER_TRANSLATOR[data['condition']]}"
        ]

        if 'temp_max' in data:
            if data['temp_min'] != data['temp_max']:
                res.append(f"Температура от {data['temp_min']} до {data['temp_max']}°С")
            else:
                res.append(f"Температура {data['temp_max']}°С")
        else:
            res.append(f"Температура {data['temp']}°С")
        res[-1] += f" (ощущается как {data['feels_like']}°С)"

        res += [
            f"Ветер {WEATHER_WIND_DIRECTION_TRANSLATOR[data['wind_dir']]} {data['wind_speed']}м/c (порывы до {data['wind_gust']}м/c)",
            f"Давление {data['pressure_mm']}мм.рт.ст.",
            f"Влажность {data['humidity']}%"
        ]

        if data.get('prec_mm', 0) != 0:
            res.append(
                f"Осадки {data['prec_mm']}мм на протяжении {int(int(data['prec_period']) / 60)} часов с вероятностью {data['prec_prob']}%"
            )

        return "\n".join(res)

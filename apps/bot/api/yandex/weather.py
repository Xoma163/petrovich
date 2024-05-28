from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PWarning
from apps.service.models import City
from petrovich.settings import env


class YandexWeather(API):
    URL = "https://api.weather.yandex.ru/v2/informers"
    TOKEN = env.str("YANDEX_WEATHER_TOKEN")
    HEADERS = {
        'X-Yandex-API-Key': TOKEN
    }

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

    def get_weather_str(self, city: City) -> str:
        data = self._get_weather(city)

        parts = [data['fact']] + data['forecast']['parts']

        weather_list = [self._get_weather_part_str(x) for x in parts]
        weather_str = "\n\n".join(weather_list)
        return f"Погода. {city.name}.\n\n" \
               f"{weather_str}"

    def _get_weather(self, city: City) -> dict:
        params = {
            'lat': city.lat,
            'lon': city.lon,
            'lang': 'ru_RU'
        }
        r = self.requests.get(self.URL, params, headers=self.HEADERS).json()

        if 'status' in r:
            if r['status'] == 403:
                raise PWarning("На сегодня я исчерпал все запросы к Yandex Weather :(")

        return r

    def _get_weather_part_str(self, data: dict) -> str:
        res = []
        # self.DAY_TRANSLATOR

        if 'part_name' in data:
            res.append(f"Прогноз на {self.DAY_TRANSLATOR[data['part_name']]}:")
        else:
            res.append(f"Сейчас:")

        res.append(f"{self.WEATHER_TRANSLATOR[data['condition']]}")

        if 'temp_max' in data:
            if data['temp_min'] != data['temp_max']:
                res.append(f"Температура от {data['temp_min']} до {data['temp_max']}°С")
            else:
                res.append(f"Температура {data['temp_max']}°С")
        else:
            res.append(f"Температура {data['temp']}°С")
        res[-1] += f" (ощущается как {data['feels_like']}°С)"

        res += [
            f"Ветер {self.WEATHER_WIND_DIRECTION_TRANSLATOR[data['wind_dir']]} {data['wind_speed']}м/c (порывы до {data['wind_gust']}м/c)",
            f"Давление {data['pressure_mm']}мм.рт.ст.",
            f"Влажность {data['humidity']}%"
        ]

        if data.get('prec_mm', 0) != 0:
            res.append(
                f"Осадки {data['prec_mm']}мм на протяжении {int(int(data['prec_period']) / 60)} часов с вероятностью {data['prec_prob']}%"
            )

        return "\n".join(res)

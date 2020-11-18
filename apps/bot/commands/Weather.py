import json

from apps.bot.APIs.YandexWeatherAPI import YandexWeatherAPI
from apps.bot.classes.Consts import WEATHER_TRANSLATOR, DAY_TRANSLATOR
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.service.models import City, Service


class Weather(CommonCommand):
    def __init__(self):
        names = ["погода"]
        help_text = "Погода - прогноз погоды"
        detail_help_text = "Погода [город=из профиля] - прогноз погоды\n" \
                           "Погода [город=из профиля] изм/изменения - изменения погоды по сравнению со вчерашним днём. " \
                           "Работает не для всех городов"
        keyboard = {'text': 'Погода', 'color': 'blue', 'row': 1, 'col': 1}
        super().__init__(names, help_text, detail_help_text, keyboard=keyboard)

    def start(self):
        changes = False
        if self.event.args and self.event.args[-1].find("изм") >= 0:
            changes = True
            del self.event.args[-1]
        if self.event.args:
            city = City.objects.filter(synonyms__icontains=self.event.original_args).first()
            if not city:
                raise RuntimeWarning("Не нашёл такой город")
        else:
            city = self.event.sender.city
        self.check_city(city)

        # Изменения погоды теперь слиты в одну команду с погодой
        if changes:
            return self.weather_changes(city)
        yandexweather_api = YandexWeatherAPI(city)
        weather_data = yandexweather_api.get_weather()
        weather_str = get_weather_str(city, weather_data)
        return weather_str

    def weather_changes(self, city):
        entity_yesterday = Service.objects.filter(name=f'weatherchange_yesterday_{city.name}')
        if not entity_yesterday.exists():
            raise RuntimeWarning("Не нашёл вчерашней погоды для этого города.")
        yandexweather_api = YandexWeatherAPI(city)

        weather_yesterday = json.loads(entity_yesterday.first().value)
        weather_today = yandexweather_api.get_weather()
        parts_yesterday = self.get_parts(weather_yesterday)
        parts_today = self.get_parts(weather_today)

        difference_total = []
        for part in parts_today:
            yesterday_part = self.get_part_for_type(weather_yesterday, part)
            today_part = self.get_part_for_type(weather_today, part)
            difference_for_part = ""

            # Если погода не ясная или не облачная
            clear_weather_statuses = ['clear', 'partly-cloudy', 'cloudy', 'overcast']
            if today_part['condition'] not in clear_weather_statuses:
                weather_today_str = WEATHER_TRANSLATOR[today_part['condition']].lower()
                difference_for_part += f"Ожидается {weather_today_str}\n"

            if part in parts_yesterday:
                avg_temp_yesterday = self.get_avg_temp(yesterday_part)
                avg_temp_today = self.get_avg_temp(today_part)

                # Изменение температуры на 5 градусов
                delta_temp = avg_temp_today - avg_temp_yesterday
                if delta_temp >= 5:
                    difference_for_part += f"Температура на {round(delta_temp)} градусов больше, чем вчера\n"
                elif delta_temp <= -5:
                    difference_for_part += f"Температура на {round(-delta_temp)} градусов меньше, чем вчера\n"

                # Разница ощущаемой и по факту температур
                delta_feels_temp = today_part['temp_feels_like'] - avg_temp_today
                if delta_feels_temp >= 5:
                    difference_for_part += f"Ощущаемая температура на {round(delta_feels_temp)} градусов больше, чем реальная\n"
                elif delta_feels_temp <= -5:
                    difference_for_part += f"Ощущаемая температура на {round(-delta_feels_temp)} градусов меньше, чем реальная\n"

                # Скорость ветра
                if today_part['wind_speed'] > 10:
                    difference_for_part += f"Скорость ветра {today_part['wind_speed']}м/с\n"
                if today_part['wind_gust'] > 20:
                    difference_for_part += f"Порывы скорости ветра до {today_part['wind_gust']}м/с\n"

            if difference_for_part:
                difference_total.append(f"Изменения на {DAY_TRANSLATOR[part]}:\n"
                                        f"{difference_for_part}")
        if not difference_total:
            return f"Нет изменений погоды в г. {city}"
        else:
            difference_str = '\n\n'.join(difference_total)
            return f"Изменения погоды в г. {city}:\n\n" \
                   f"{difference_str}"

    @staticmethod
    def get_part_for_type(weather, _type):
        if weather['now']['part_name'] == _type:
            return weather['now']
        elif weather['forecast'][0]['part_name'] == _type:
            return weather['forecast'][0]
        elif weather['forecast'][1]['part_name'] == _type:
            return weather['forecast'][1]
        return None

    @staticmethod
    def get_parts(weather):
        parts = [weather['now']['part_name']]
        for x in weather['forecast']:
            parts.append(x['part_name'])
        return parts

    @staticmethod
    def get_avg_temp(weather):
        if 'temp' in weather:
            return weather['temp']
        elif 'temp_min' in weather:
            return (weather['temp_max'] + weather['temp_min']) / 2


def get_weather_str(city, weather_data):
    now = \
        f"Погода в г. {city.name} сейчас:\n" \
        f"{WEATHER_TRANSLATOR[weather_data['now']['condition']]}\n" \
        f"Температура {weather_data['now']['temp']}°С(ощущается как {weather_data['now']['temp_feels_like']}°С)\n" \
        f"Ветер {weather_data['now']['wind_speed']}м/c(порывы до {weather_data['now']['wind_gust']}м/c)\n" \
        f"Давление {weather_data['now']['pressure']}мм.рт.ст., влажность {weather_data['now']['humidity']}%"

    forecast = ""
    for x in weather_data['forecast']:
        forecast += \
            f"\n\n" \
            f"Прогноз на {DAY_TRANSLATOR[x['part_name']]}:\n" \
            f"{WEATHER_TRANSLATOR[x['condition']]}\n"

        if x['temp_min'] != x['temp_max']:
            forecast += f"Температура от {x['temp_min']} до {x['temp_max']}°С"
        else:
            forecast += f"Температура {x['temp_max']}°С"

        forecast += \
            f"(ощущается как {x['temp_feels_like']}°С)\n" \
            f"Ветер {x['wind_speed']}м/c(порывы до {x['wind_gust']}м/c)\n" \
            f"Давление {x['pressure']} мм.рт.ст., влажность {x['humidity']}%\n"
        if x['prec_mm'] != 0:
            forecast += \
                f"Осадки {x['prec_mm']}мм " \
                f"на протяжении {x['prec_period']} часов " \
                f"с вероятностью {x['prec_prob']}%"
        else:
            forecast += "Без осадков"
    return now + forecast

from apps.bot.api.handler import API
from petrovich.settings import env


class YandexGeo(API):
    URL = "https://geocode-maps.yandex.ru/1.x/"
    API_KEY = env.str("YANDEX_GEO_TOKEN")

    def get_city_info_by_name(self, city_name) -> dict:
        params = {
            'apikey': self.API_KEY,
            'geocode': city_name,
            'format': 'json',
            'result': '1',
            'lang': 'ru_RU'
        }
        r = self.requests.get(self.URL, params).json()

        result = r['response']['GeoObjectCollection']['featureMember']
        if len(result) == 0:
            return {}
        city_data = result[0]['GeoObject']
        lon, lat = city_data['Point']['pos'].split(' ', 2)
        city_name = city_data['name']
        city_info = {
            'lat': lat,
            'lon': lon,
            'name': city_name
        }
        return city_info

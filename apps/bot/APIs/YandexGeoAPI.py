import requests

from petrovich.settings import env


class YandexGeoAPI:
    def __init__(self):
        self.url = "https://geocode-maps.yandex.ru/1.x/"
        self.API_KEY = env.str("YANDEX_GEO_TOKEN")

    def get_address(self, lat, lon):
        params = {
            'apikey': self.API_KEY,
            'geocode': f"{lat, lon}",
            'format': 'json',
            'result': '1',
            'lang': 'ru_RU'
        }
        result = requests.get(self.url, params).json()
        return result['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
            'GeocoderMetaData']['text']

    def get_city_info_by_name(self, city_name):
        params = {
            'apikey': self.API_KEY,
            'geocode': city_name,
            'format': 'json',
            'result': '1',
            'lang': 'ru_RU'
        }
        result = requests.get(self.url, params).json()
        result2 = result['response']['GeoObjectCollection']['featureMember']
        if len(result2) == 0:
            return None
        city_data = result2[0]['GeoObject']
        lon, lat = city_data['Point']['pos'].split(' ', 2)
        city_name = city_data['name']
        city_info = {
            'lat': lat,
            'lon': lon,
            'name': city_name
        }
        return city_info

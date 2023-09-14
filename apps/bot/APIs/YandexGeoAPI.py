import logging

import requests

from petrovich.settings import env

logger = logging.getLogger('bot')


class YandexGeoAPI:
    url = "https://geocode-maps.yandex.ru/1.x/"
    API_KEY = env.str("YANDEX_GEO_TOKEN")

    def get_address(self, lat, lon):
        params = {
            'apikey': self.API_KEY,
            'geocode': f"{lat, lon}",
            'format': 'json',
            'result': '1',
            'lang': 'ru_RU'
        }
        r = requests.get(self.url, params)
        logger.debug(r.content)

        return r.json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
            'GeocoderMetaData']['text']

    def get_city_info_by_name(self, city_name):
        params = {
            'apikey': self.API_KEY,
            'geocode': city_name,
            'format': 'json',
            'result': '1',
            'lang': 'ru_RU'
        }
        r = requests.get(self.url, params)
        logger.debug(r.content)

        result = r.json()['response']['GeoObjectCollection']['featureMember']
        if len(result) == 0:
            return None
        city_data = result[0]['GeoObject']
        lon, lat = city_data['Point']['pos'].split(' ', 2)
        city_name = city_data['name']
        city_info = {
            'lat': lat,
            'lon': lon,
            'name': city_name
        }
        return city_info

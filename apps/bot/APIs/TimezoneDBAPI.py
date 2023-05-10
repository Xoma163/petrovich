import requests

from petrovich.settings import env


class TimezoneDBAPI:
    URL = "https://api.timezonedb.com/v2.1/get-time-zone"
    API_KEY = env.str("TIMEZONEDB_API_KEY")

    def get_timezone_by_coordinates(self, lat, lon):
        params = {
            'key': self.API_KEY,
            'format': 'json',
            'by': 'position',
            'lat': lat,
            'lng': lon
        }
        result = requests.get(self.URL, params=params).json()
        return result['zoneName']

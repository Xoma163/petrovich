from apps.bot.api.handler import API
from petrovich.settings import env


class TimezoneDB(API):
    URL = "https://api.timezonedb.com/v2.1/get-time-zone"
    API_KEY = env.str("TIMEZONEDB_API_KEY")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_timezone_by_coordinates(self, lat: str, lon: str) -> str:
        params = {
            'key': self.API_KEY,
            'format': 'json',
            'by': 'position',
            'lat': lat,
            'lng': lon
        }
        r = self.requests.get(self.URL, params=params).json()

        return r['zoneName']

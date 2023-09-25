import logging

import requests

from petrovich.settings import env

logger = logging.getLogger('responses')


class TimezoneDB:
    URL = "https://api.timezonedb.com/v2.1/get-time-zone"
    API_KEY = env.str("TIMEZONEDB_API_KEY")

    def get_timezone_by_coordinates(self, lat: str, lon: str) -> str:
        params = {
            'key': self.API_KEY,
            'format': 'json',
            'by': 'position',
            'lat': lat,
            'lng': lon
        }
        r = requests.get(self.URL, params=params).json()
        logger.debug({"response": r})

        return r['zoneName']

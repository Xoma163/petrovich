import logging

import requests

logger = logging.getLogger('bot')


class FuckingGreatAdviceAPI:
    URL = "https://fucking-great-advice.ru/api/random"

    def get_advice(self):
        r = requests.get(self.URL)
        logger.debug(r.content)

        return r.json()['text']

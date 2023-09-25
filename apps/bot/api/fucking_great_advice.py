import logging

import requests

logger = logging.getLogger('bot')


class FuckingGreatAdvice:
    URL = "https://fucking-great-advice.ru/api/random"

    def get_advice(self):
        r = requests.get(self.URL).json()
        logger.debug({"response": r})

        return r['text']

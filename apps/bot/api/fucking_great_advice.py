import logging

import requests

logger = logging.getLogger('responses')


class FuckingGreatAdvice:
    URL = "https://fucking-great-advice.ru/api/random"

    def get_advice(self) -> str:
        r = requests.get(self.URL).json()
        logger.debug({"response": r})

        return r['text']

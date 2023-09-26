import logging

import requests

from apps.bot.classes.const.exceptions import PError, PWarning
from petrovich.settings import env

logger = logging.getLogger('responses')


class OCR:
    URL = 'https://api.ocr.space/parse/image'
    API_KEY = env.str("OCR_API_KEY")

    ERROR_CODE = 99

    def recognize(self, file: bytes, lang: str) -> str:
        payload = {
            'filetype': 'JPG',
            'apikey': self.API_KEY,
            'language': lang,
        }
        r = requests.post(self.URL, files={'filename.jpg': file}, data=payload).json()
        logger.debug({"response": r})

        if 'OCRExitCode' in r and r['OCRExitCode'] == self.ERROR_CODE:
            raise PError("Ошибка API")
        if 'ParsedResults' not in r:
            raise PWarning("Ничего не распознал")
        text_list = [x['ParsedText'].strip() for x in r['ParsedResults']]
        texts = "\n".join(text_list)
        return texts

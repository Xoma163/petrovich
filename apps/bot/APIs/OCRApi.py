import logging

import requests

from apps.bot.classes.consts.Exceptions import PError, PWarning
from petrovich.settings import env

logger = logging.getLogger('bot')


class OCRApi:
    URL = 'https://api.ocr.space/parse/image'
    API_KEY = env.str("OCR_API_KEY")

    def get_recognize_by_bytes(self, file, language):
        payload = {
            'filetype': 'JPG',
            'apikey': self.API_KEY,
            'language': language,
        }
        r = requests.post(self.URL, files={'filename.jpg': file}, data=payload)
        logger.debug(r.content)

        return r.json()

    def recognize(self, url_or_bytes, lang):
        r = self.get_recognize_by_bytes(url_or_bytes, lang)

        if 'OCRExitCode' in r:
            if r['OCRExitCode'] == 99:
                raise PError("Ошибка")
        if 'ParsedResults' not in r:
            raise PWarning("Ничего не распознал")
        text_list = [x['ParsedText'].strip() for x in r['ParsedResults']]
        texts = "\n".join(text_list)
        return texts

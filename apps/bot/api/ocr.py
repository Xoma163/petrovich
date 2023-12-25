from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PError, PWarning
from petrovich.settings import env


class OCR(API):
    URL = 'https://api.ocr.space/parse/image'
    API_KEY = env.str("OCR_API_KEY")

    ERROR_CODE = 99

    def recognize(self, file: bytes, lang: str) -> str:
        payload = {
            'filetype': 'JPG',
            'apikey': self.API_KEY,
            'language': lang,
        }
        r = self.requests.post(self.URL, files={'filename.jpg': file}, data=payload).json()

        if 'OCRExitCode' in r and r['OCRExitCode'] == self.ERROR_CODE:
            raise PError("Ошибка API")
        if 'ParsedResults' not in r:
            raise PWarning("Ничего не распознал")
        text_list = [x['ParsedText'].strip() for x in r['ParsedResults']]
        texts = "\n".join(text_list)
        return texts

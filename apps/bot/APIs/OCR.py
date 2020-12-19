import requests

# https://ocr.space/OCRAPI
from apps.bot.classes.Exceptions import PError, PWarning
from petrovich.settings import env


class OCRApi:
    def __init__(self):
        self.url = 'https://api.ocr.space/parse/image'
        self.api_key = env.str("OCR_API_KEY")

    def get_recognize_by_url(self, url, language):
        payload = {
            'url': url,
            'apikey': self.api_key,
            'language': language,
        }
        return requests.post('https://api.ocr.space/parse/image',
                             data=payload,
                             ).json()

    def get_recognize_by_bytes(self, file, language):
        payload = {
            'filetype': 'JPG',
            'apikey': self.api_key,
            'language': language,
        }
        return requests.post('https://api.ocr.space/parse/image',
                             files={'filename.jpg': file},
                             data=payload,
                             ).json()

    def recognize(self, url_or_bytes, lang):
        if isinstance(url_or_bytes, str):
            response = self.get_recognize_by_url(url_or_bytes, lang)
        else:
            response = self.get_recognize_by_bytes(url_or_bytes, lang)

        if 'OCRExitCode' in response:
            if response['OCRExitCode'] == 99:
                raise PError("Ошибка")
        if 'ParsedResults' not in response:
            raise PWarning("Ничего не распознал")
        text_list = [x['ParsedText'].strip() for x in response['ParsedResults']]
        texts = "\n".join(text_list)
        return texts

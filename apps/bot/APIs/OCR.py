import requests

from apps.bot.classes.consts.Exceptions import PError, PWarning
from petrovich.settings import env


class OCRApi:
    URL = 'https://api.ocr.space/parse/image'
    API_KEY = env.str("OCR_API_KEY")

    # def get_recognize_by_url(self, url, language):
    #     payload = {
    #         'url': url,
    #         'apikey': self.API_KEY,
    #         'language': language,
    #     }
    #     return requests.post(
    #         self.URL,
    #         data=payload,
    #     ).json()

    def get_recognize_by_bytes(self, file, language):
        payload = {
            'filetype': 'JPG',
            'apikey': self.API_KEY,
            'language': language,
        }
        return requests.post(
            self.URL,
            files={'filename.jpg': file},
            data=payload,
        ).json()

    def recognize(self, url_or_bytes, lang):
        response = self.get_recognize_by_bytes(url_or_bytes, lang)

        if 'OCRExitCode' in response:
            if response['OCRExitCode'] == 99:
                raise PError("Ошибка")
        if 'ParsedResults' not in response:
            raise PWarning("Ничего не распознал")
        text_list = [x['ParsedText'].strip() for x in response['ParsedResults']]
        texts = "\n".join(text_list)
        return texts

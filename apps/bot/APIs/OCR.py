import requests

# https://ocr.space/OCRAPI
from petrovich.settings import env


# ToDo: url or content
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
        response = requests.post('https://api.ocr.space/parse/image',
                                 data=payload,
                                 ).json()
        return response

    def get_recognize_by_bytes(self, file, language):
        payload = {
            'filetype': 'JPG',
            'apikey': self.api_key,
            'language': language,
        }
        response = requests.post('https://api.ocr.space/parse/image',
                                 files={'filename.jpg': file},
                                 data=payload,
                                 ).json()
        return response

    def recognize(self, url_or_bytes, lang):
        if isinstance(url_or_bytes, str):
            response = self.get_recognize_by_url(url_or_bytes, lang)
        else:
            response = self.get_recognize_by_bytes(url_or_bytes, lang)

        if 'OCRExitCode' in response:
            if response['OCRExitCode'] == 99:
                raise RuntimeWarning("Неправильный язык")
        if 'ParsedResults' not in response:
            raise RuntimeWarning("Ничего не распознал")
        text_list = [x['ParsedText'].strip() for x in response['ParsedResults']]
        texts = "\n".join(text_list)
        return texts

import requests

# https://ocr.space/OCRAPI
from petrovich.settings import env


class OCRApi:
    def __init__(self):
        self.url = 'https://api.ocr.space/parse/image'
        self.api_key = env.str("OCR_API_KEY")

    def recognize(self, image_url, lang):
        payload = {'url': image_url,
                   'apikey': self.api_key,
                   'language': lang,
                   }
        response = requests.post('https://api.ocr.space/parse/image',
                                 data=payload,
                                 ).json()
        if 'OCRExitCode' in response:
            if response['OCRExitCode'] == 99:
                raise RuntimeWarning("Неправильный язык")
        if 'ParsedResults' not in response:
            raise RuntimeWarning("Ничего не распознал")
        text_list = [x['ParsedText'].strip() for x in response['ParsedResults']]
        texts = "\n".join(text_list)
        return texts

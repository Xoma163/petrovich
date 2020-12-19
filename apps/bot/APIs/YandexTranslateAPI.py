import requests

from apps.bot.classes.Exceptions import PWarning
from petrovich.settings import env


class YandexTranslateAPI:
    def __init__(self):
        self.url = "https://translate.yandex.net/api/v1.5/tr.json/translate"
        self.TOKEN = env.str("YANDEX_TRANSLATE_TOKEN")

    def get_translate(self, lang, text):
        params = {
            'lang': lang,
            'key': self.TOKEN,
            'text': text
        }
        response = requests.get(self.url, params).json()
        if response['code'] != 200:
            raise PWarning(f"Ошибка:\n{response}")
        return response['text'][0]

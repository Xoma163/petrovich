import requests


class RzhunemoguAPI:
    def __init__(self):
        self.URL = "http://rzhunemogu.ru/RandJSON.aspx"

    def get_joke(self, _type=1):
        params = {
            'CType': _type
        }
        response = requests.get(self.URL, params, timeout=10)

        if response.status_code != 200:
            raise RuntimeWarning("Чёто не работает. Пинайте этого лентяя")

        # Потому что от апи ответ гавённый и не jsonится
        return response.text.replace('{"content":"', '').replace('"}', '')

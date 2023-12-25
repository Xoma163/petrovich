import logging

from bs4 import BeautifulSoup

from apps.bot.api.handler import API

logger = logging.getLogger('api')


class CBRAPI(API):
    URL = "https://www.cbr-xml-daily.ru/daily.xml"

    def __init__(self, filters_list):
        super().__init__()
        self.filters = {x: {
            'name': None,
            'value': 0.0
        } for x in filters_list}

    def get_ex_rates(self) -> dict:
        r = self.requests.get(self.URL, stream=True)
        elements = BeautifulSoup(r.content, 'xml').find('ValCurs').find_all("Valute")

        for elem in elements:
            for _filter in self.filters:
                if elem.find("CharCode").text == _filter:
                    self.filters[_filter]['name'] = elem.find('Name').text.lower()
                    self.filters[_filter]['value'] = float(elem.find("Value").text.replace(',', '.')) / float(
                        elem.find("Nominal").text.replace(',', '.'))

        return self.filters

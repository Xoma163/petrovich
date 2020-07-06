import requests
from bs4 import BeautifulSoup, NavigableString


class BashAPI:
    def __init__(self, count):
        self.count = count
        self.URL = 'http://bash.im/random'

    def parse(self):
        r = requests.get(self.URL)
        bsop = BeautifulSoup(r.text, 'html.parser')
        html_quotes = bsop.find('section', {'class': 'quotes'}).find_all('div', {'class': 'quote__body'})[:self.count]
        bash_quotes = []

        for quote in html_quotes:
            text_quotes = []
            for content in quote.contents:
                if isinstance(content, NavigableString):
                    text_quotes.append(content.strip())
            bash_quotes.append("\n".join(text_quotes))
        return "\n——————————————————\n".join(bash_quotes)

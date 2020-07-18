import time

import requests


class Covid19API:

    def __init__(self, country_name):
        self.country_name = country_name
        self.TRIES = 10

    def do_the_request(self, url, **kwargs):
        status_code = None
        response = None
        while self.TRIES > 0 and status_code != 200:
            response = requests.get(url, **kwargs)
            self.TRIES -= 1
            status_code = response.status_code
            time.sleep(1)
        return response

    def get_detail_by_country(self):
        url = f"https://api.covid19api.com/total/country/{self.country_name}"
        try:
            response = self.do_the_request(url, timeout=10)
            time.sleep(1)
        except requests.exceptions.ReadTimeout:
            raise RuntimeError("Проблемы с API. Слишком долго ждал")
        if not response:
            raise RuntimeError(f"Проблемы с API. {response.status_code}")
        response = response.json()

        # Суммирование сгрупированных данных
        data = {'Confirmed': [], 'Deaths': [], "Recovered": [], "Dates": [], 'Active': []}
        for item in response:
            data['Active'].append(item['Active'])
            data['Confirmed'].append(item['Confirmed'])
            data['Deaths'].append(item['Deaths'])
            data['Recovered'].append(item['Recovered'])
            data['Dates'].append(item['Date'])
        return data

    def get_by_country(self):
        def set_data(data):
            return f"Сегодня:\n" \
                   f"Заболело - {data['NewConfirmed']}\n" \
                   f"Смертей - {data['NewDeaths']}\n" \
                   f"Выздоровело - {data['NewRecovered']}\n" \
                   f"\n" \
                   f"На данный момент:\n" \
                   f"Заболело - {data['TotalConfirmed']}\n" \
                   f"Смертей - {data['TotalDeaths']}\n" \
                   f"Выздоровело - {data['TotalRecovered']}\n" \
                   f"Болеют сейчас - {data['TotalConfirmed'] - data['TotalDeaths'] - data['TotalRecovered']}\n"

        url = "https://api.covid19api.com/summary"
        try:
            response = self.do_the_request(url, timeout=10)
        except requests.exceptions.ReadTimeout:
            raise RuntimeError("Проблемы с API. Слишком долго ждал")
        if not response:
            raise RuntimeError(f"Проблемы с API. {response.status_code}")
        response = response.json()

        if self.country_name is None:
            return set_data(response["Global"])

        for country in response['Countries']:
            if country['Slug'].lower() == self.country_name.lower():
                return set_data(country)
        return None

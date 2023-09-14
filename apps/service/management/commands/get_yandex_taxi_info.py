import requests
from django.core.management import BaseCommand

from apps.service.models import TaxiInfo
from petrovich.settings import env


class Command(BaseCommand):

    def __init__(self):
        super().__init__()

    def handle(self, *args, **kwargs):
        url = "https://taxi-routeinfo.taxi.yandex.net/taxi_info"
        params = {
            'clid': env.str('YANDEX_TAXI_CLID'),
            'apikey': env.str('YANDEX_TAXI_API_KEY'),
            'rll': env.str('YANDEX_TAXI_TEST_COORDS'),
            'class': 'econom,business,comfortplus,express,courier',
        }
        r = requests.get(url, params)
        TaxiInfo(data=r.json()).save()

from django.db import ConnectionRouter

from apps.service.models import TaxiInfo
from petrovich.settings import TAXI_DB


# noqa
class TaxiDBRouter(ConnectionRouter):
    def db_for_read(self, model, **kwargs):
        if model == TaxiInfo:
            return TAXI_DB
        return None

    def db_for_write(self, model, **kwargs):
        if model == TaxiInfo:
            return TAXI_DB
        return None

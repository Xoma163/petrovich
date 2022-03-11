from apps.service.models import TaxiInfo
from petrovich.settings import TAXI_DB


class TaxiDBRouter:
    def db_for_read(self, model, **hints):
        if model == TaxiInfo:
            return TAXI_DB
        return None

    def db_for_write(self, model, **hints):
        if model == TaxiInfo:
            return TAXI_DB
        return None

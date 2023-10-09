from apps.service.models import TaxiInfo
from petrovich.settings import TAXI_DB


class TaxiDBRouter:
    @staticmethod
    def db_for_read(model):
        if model == TaxiInfo:
            return TAXI_DB
        return None

    @staticmethod
    def db_for_write(model):
        if model == TaxiInfo:
            return TAXI_DB
        return None

import datetime

from django.core.management.base import BaseCommand

from apps.db_logger.models import Logger

LOGS_PERIOD = 30


class Command(BaseCommand):

    def handle(self, *args, **options):
        logs = Logger.objects.filter(create_datetime__lte=datetime.datetime.utcnow() - datetime.timedelta(
                                         days=LOGS_PERIOD))
        logs.delete()

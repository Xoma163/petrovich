import datetime

from django.core.management.base import BaseCommand

from apps.service.models import Promocode


class Command(BaseCommand):

    def handle(self, *args, **options):
        dt_now = datetime.datetime.now().date()
        promocodes = Promocode.objects.filter(expiration__lt=dt_now)

        for promocode in promocodes:
            promocode.delete()

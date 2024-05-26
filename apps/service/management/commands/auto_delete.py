import datetime

from django.core.management.base import BaseCommand

from apps.service.models import VideoCache, Promocode


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.delete_video_caches()
        self.delete_promocodes()

    @staticmethod
    def delete_video_caches():
        DAYS = 30
        dt = datetime.datetime.now().date() - datetime.timedelta(days=DAYS)
        VideoCache.objects.filter(created_at__lte=dt).delete()

    @staticmethod
    def delete_promocodes():
        dt_now = datetime.datetime.now().date()
        Promocode.objects.filter(expiration__lt=dt_now).delete()

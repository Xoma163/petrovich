import datetime

from django.core.management.base import BaseCommand

from apps.bot.models import ProfileSettings, ChatSettings
from apps.commands.media_command.models import VideoCache


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.delete_video_caches()
        self.delete_unattached_settings()

    @staticmethod
    def delete_video_caches():
        DAYS = 30
        dt = datetime.datetime.now().date() - datetime.timedelta(days=DAYS)
        VideoCache.objects.filter(created_at__lte=dt).delete()

    # ToDo: Костыль
    @staticmethod
    def delete_unattached_settings():
        """
        Костыль по удалению настроек, которые не привязаны
        """
        ProfileSettings.objects.filter(profile__isnull=True).delete()
        ChatSettings.objects.filter(chat__isnull=True).delete()

from django.core.management.base import BaseCommand

from apps.bot.models import UserSettings, ChatSettings, User


class Command(BaseCommand):

    def handle(self, *args, **options):
        UserSettings.objects.filter(profile__isnull=True).delete()
        ChatSettings.objects.filter(chat__isnull=True).delete()
        User.objects.filter(profile__isnull=True).delete()

from django.core.management.base import BaseCommand

from apps.bot.models import Profile


class Command(BaseCommand):
    def handle(self, *args, **options):
        for profile in Profile.objects.all():
            profile.gamer2 = profile.gamer
            profile.save()
        print()

from datetime import timedelta

from django.core.management.base import BaseCommand

from apps.games.models import PetrovichGames


class Command(BaseCommand):
    def handle(self, *args, **options):
        games = PetrovichGames.objects.filter(chat__pk=1, date__year=2021)
        for game in games:
            game.date = game.date - timedelta(days=365)
            game.save()

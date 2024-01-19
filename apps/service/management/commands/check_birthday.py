from django.core.management.base import BaseCommand

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.models import Profile
from apps.games.models import Gamer

tg_bot = TgBot()


class Command(BaseCommand):
    def handle(self, *args, **options):
        for profile in Profile.objects.all():
            if profile.gamer:
                continue
            gamer = Gamer(profile=profile)
            gamer.save()

from django.core.management.base import BaseCommand

from apps.bot.models import Chat
from apps.games.models import PetrovichGames


class Command(BaseCommand):
    def handle(self, *args, **options):
        games = PetrovichGames.objects.filter(chat__pk=1)
        new_chat = Chat.objects.get(pk=46)
        for game in games:
            game.chat = new_chat
            game.save()

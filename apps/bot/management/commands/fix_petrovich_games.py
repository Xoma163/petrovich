import datetime
from itertools import groupby

from django.core.management import BaseCommand

from apps.games.models import PetrovichUser, PetrovichGames


class Command(BaseCommand):

    def __init__(self):
        super().__init__()

    def handle(self, *args, **kwargs):
        PetrovichGames.objects.all().delete()
        pus = PetrovichUser.objects.filter(chat__isnull=False).order_by('chat_id')
        for chat, group_items in groupby(pus, key=lambda x: x.chat):
            date = datetime.datetime(2021, 1, 1)
            for user in group_items:
                for _ in range(user.wins):
                    pg = PetrovichGames.objects.create(
                        profile=user.profile,
                        chat=chat,
                    )
                    pg.date = date.date()
                    pg.save()

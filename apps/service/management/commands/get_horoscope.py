from django.core.management import BaseCommand

from apps.service.models import Meme, Horoscope

MEMES_COUNT = 12


class Command(BaseCommand):

    def handle(self, *args, **options):
        random_memes = Meme.objects.exclude(type='audio').order_by('?')[:MEMES_COUNT]
        if len(random_memes) != MEMES_COUNT:
            return
        Horoscope.objects.all().delete()
        horoscope = Horoscope()
        horoscope.save()
        horoscope.memes.add(*random_memes)
        horoscope.save()

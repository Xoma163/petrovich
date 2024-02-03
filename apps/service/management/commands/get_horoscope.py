from django.core.management import BaseCommand

from apps.service.models import Meme, Horoscope, HoroscopeMeme

MEMES_COUNT = 12


class Command(BaseCommand):

    def handle(self, *args, **options):
        HoroscopeMeme.objects.all().delete()
        random_memes = Meme.objects.exclude(type='audio', approved=False).exclude(for_trusted=True).order_by('?')[
                       :MEMES_COUNT]
        if len(random_memes) != MEMES_COUNT:
            return

        hms = []
        for meme in random_memes:
            meme_dict = meme.__dict__
            del meme_dict['_state']
            pk = meme_dict.pop('id')
            hm = HoroscopeMeme(**meme_dict)
            hm.meme_pk = pk
            hm.save()
            hms.append(hm)

        Horoscope.objects.all().delete()
        horoscope = Horoscope()
        horoscope.save()
        for hm in hms:
            horoscope.memes.add(hm)
        horoscope.save()

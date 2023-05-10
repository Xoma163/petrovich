from django.core.management import BaseCommand

from apps.service.models import Meme


class Command(BaseCommand):
    pass

    def handle(self, *args, **options):
        memes = Meme.objects.filter(type__in=['photo', 'sticker'], tg_file_id__isnull=False)

        for i, meme in enumerate(memes):
            meme.link = ""
            meme.save()
